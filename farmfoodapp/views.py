import datetime
import pytz
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from farmfoodapp.models import RegisterModel, VendorManager, VendorProduct, CostManager
from farmfoodapp.models import VendorInventory, ProductViews, VendorBlogs
from farmfoodapp.app_serializers import RegisterSerializer, VendorProductSer
from farmfoodapp.actions import check_existing_user, check_login_attempts, reduce_login_attempts, decode_token, \
    send_verification_email, send_forget_pass_email, make_data_dict
from rest_framework.decorators import api_view
from fuzzywuzzy import fuzz

utc = pytz.UTC


# Create your views here.

@api_view(["POST", "GET"])
def register_api(request):
    try:
        data = request.data
        user_data = data.copy()
        if user_data['user_password'] != user_data['user_password_cnf']:
            return render(request, 'onboarding/User_Registration.html', {'msg': 'Passwords Do Not Match'})
        if check_existing_user(user_data['email']):
            return render(request, 'onboarding/User_Registration.html', {"msg": "User Already Exist"})
        user_data['user_password'] = make_password(user_data['user_password'])
        data_serializer = RegisterSerializer(data=user_data)
        if data_serializer.is_valid():
            data_serializer.save()
            send_verification_email(user_data, user_data['email'])
            return render(request, 'success/Page_Success.html',
                          {"msg": "Please Check Your Account for Activation Link"})
        else:
            return HttpResponse("Something Went Wrong")
    except Exception as e:
        return render(request, 'onboarding/User_Registration.html',
                      {"msg": "Something Went Wrong, Try Again in Some Time, " + str(e)})


@api_view(["POST", "GET"])
def login_api(request):
    try:
        user_data = request.data
        if not check_existing_user(user_data['email']):
            return render(request, 'onboarding/User_Login.html', {"msg": "User Not Registered"})
        data = RegisterModel.objects.get(email=user_data['email'])
        json_data = RegisterSerializer(data)
        json_data = json_data.data
        if data.account_status == "inactive":
            return render(request, 'onboarding/User_Login.html', {"msg": "Account Inactive, Please Confirm Email"})
        attempts, time_lock = check_login_attempts(user_data['email'])
        if attempts == 0:
            return render(request, 'onboarding/User_Login.html', {"msg": "Account Permanently Locked"})
        if not utc.localize(datetime.datetime.now()) > time_lock:
            time_remaining = str(time_lock - utc.localize(datetime.datetime.now()))
            return render(request, 'onboarding/User_Login.html',
                          {"msg": "Account Temporarily Locked, Try Again In " + str(time_remaining[2:4]) + " Minutes"})
        if check_password(user_data['user_password'], data.user_password):
            data.attempts_left = 10
            data.save()
            user_id = data.id
            json_data["id"] = user_id
            request.session["login_session_data"] = json_data
            return HttpResponseRedirect(reverse('home-page'))
        else:
            reduce_login_attempts(user_data['email'], attempts)
            return render(request, 'onboarding/User_Login.html',
                          {"msg": "Login Unsuccessful, Incorrect Password, Attempts Left:" + str(attempts - 1)})
    except Exception as e:
        return HttpResponse("SOMETHING WENT WRONG " + str(e))


def register_view(request):
    return render(request, 'onboarding/User_Registration.html')


def login_view(request):
    if "msg" in request.session:
        msg = {"msg": request.session['msg']}
        del request.session["msg"]
        return render(request, 'onboarding/User_Login.html', msg)
    return render(request, 'onboarding/User_Login.html')


def home_page(request):
    if "login_session_data" in request.session:
        isFarmer = RegisterModel.objects.get(email=request.session["login_session_data"]["email"])
        data = VendorProduct.objects.all()
        data_list = [{
            "id": prod.id,
            "product_name": prod.product_name,
            "category": prod.category,
            "description": prod.description,
            "price": float("{:.2f}".format(prod.price)),
            "image": prod.image
        } for prod in data]
        return render(request, 'home/HomePage.html',
                      {"products": data_list, "first_name": request.session["login_session_data"]["first_name"],
                       "is_farmer": isFarmer.is_farmer})
    else:
        return HttpResponseRedirect(reverse('login-view'))


@api_view(['GET', 'POST'])
def forget_password_view(request):
    if request.method == "GET":
        return render(request, 'onboarding/User_ForgetPassword.html')
    if request.method == "POST":
        data = request.data
        user_count = RegisterModel.objects.filter(email=data['email']).count()
        if user_count == 0:
            return render(request, 'onboarding/User_ForgetPassword.html', {"msg": "User Does Not Exist"})
        else:
            user = RegisterModel.objects.get(email=data['email'])
            payload = {
                'email': user.email,
                'phone': user.phone,
            }
            send_forget_pass_email(payload, user.email)
        return render(request, 'success/Page_Success.html',
                      {"msg": "Please Check Your Email for the RESET Link"})


def reset_password_view(request, token):
    if request.method == "GET":
        result, data = decode_token(token)
        if result:
            request.session["data"] = data
            return render(request, 'onboarding/User_ResetPassword.html')
        else:
            return HttpResponse("INVALID URL")
    else:
        return HttpResponse("METHOD NOT ALLOWED")


@api_view(['POST'])
def reset_password_api(request):
    if request.method == "POST" and "data" in request.session:
        user_pass = request.data
        if user_pass["user_password"] == user_pass["user_password_cnf"]:
            data = request.session["data"]
            user = RegisterModel.objects.get(email=data['email'])
            user.user_password = make_password(user_pass['user_password'])
            user.save()
            del request.session["data"]
            request.session["msg"] = "Password Reset Successful, Please Login"
            return HttpResponseRedirect(reverse('login-view'))
        else:
            return render(request, 'onboarding/User_ResetPassword.html', {"msg": "Passwords Dont Match"})
    else:
        return HttpResponse("METHOD NOT ALLOWED")


def verify_reg_email(request, token):
    if request.method == "GET":
        result, data = decode_token(token)
        if result:
            user = RegisterModel.objects.get(email=data['email'])
            user.account_status = "active"
            user.attempts_left = 10
            user.save()
            request.session["msg"] = "Account Successfully Verified"
            return HttpResponseRedirect(reverse('login-view'))
        else:
            return HttpResponse("<h2>Invalid URL</h2>")
    else:
        return HttpResponse("METHOD NOT ALLOWED")


@api_view(['GET', 'POST'])
def add_product_view(request):
    if request.method == 'GET':
        if "login_session_data" in request.session:
            return render(request, 'products/Add_Product.html',
                          {"first_name": request.session["login_session_data"]["first_name"]})
        else:
            return HttpResponseRedirect(reverse('login-view'))
    if request.method == "POST":
        if "login_session_data" in request.session:
            user_data = request.data
            login_data = request.session["login_session_data"]
            vp_obj = VendorProduct(user_id=RegisterModel.objects.get(id=login_data["id"]),
                                   product_name=user_data["product_name"],
                                   category=user_data["category"],
                                   description=user_data["description"],
                                   price=user_data["price"],
                                   image=user_data["image"])
            vp_obj.save()
            return HttpResponseRedirect(reverse('view_products'))


@api_view(['GET', 'POST'])
def onboard_vendor_view_api(request):
    if request.method == "GET":
        if "login_session_data" in request.session:
            return render(request, 'onboarding/Onboard_Farmer.html')
        else:
            return HttpResponseRedirect(reverse('login-view'))
    if request.method == "POST":
        if "login_session_data" in request.session:
            user_data = request.data
            login_data = request.session["login_session_data"]
            vendor_obj = VendorManager(user=RegisterModel.objects.get(id=login_data["id"]),
                                       company_name=user_data["company_name"],
                                       location=user_data["location"],
                                       market_name=user_data['market_name'],
                                       address=user_data["address"])
            vendor_obj.save()
            reg_obj = RegisterModel.objects.get(id=login_data["id"])
            reg_obj.is_farmer = True
            reg_obj.save()
            return HttpResponseRedirect(reverse('dashboard'))


def view_products(request):
    if "login_session_data" in request.session:
        login_data = request.session["login_session_data"]
        isFarmer = RegisterModel.objects.get(id=login_data["id"])
        isFarmer = isFarmer.is_farmer
        reg_data = VendorProduct.objects.filter(user_id=login_data["id"])
        json_data = [{
            "product_name": i.product_name,
            "category": i.category,
            "description": i.description,
            "price": float("{:.2f}".format(i.price)),
            "id": i.id
        }
            for i in reg_data]
        return render(request, 'products/View_Product_Page.html', {"data": json_data, "is_farmer": isFarmer,
                                                                   "first_name": request.session["login_session_data"][
                                                                       "first_name"]})
    else:
        return HttpResponseRedirect(reverse('login-view'))


@api_view(["GET", "POST"])
def edit_product(request, prod_id):
    if "login_session_data" in request.session:
        if request.method == "GET":
            data = VendorProduct.objects.get(id=prod_id)
            p_id = data.id
            ser = VendorProductSer(data)
            data = ser.data
            data["id"] = p_id
            data["first_name"] = request.session["login_session_data"]["first_name"]
            return render(request, "products/Edit_Product.html", data)
        if request.method == "POST":
            data = request.data
            obj = VendorProduct.objects.get(id=prod_id)
            obj.product_name = data['product_name']
            obj.category = data['category']
            obj.description = data['description']
            obj.price = data['price']
            if data["image"] == "":
                obj.save()
            else:
                obj.image = data['image']
                obj.save()
            return HttpResponseRedirect(reverse('view_products'))
    else:
        return HttpResponseRedirect(reverse('login-view'))


def delete_product(request, prod_id):
    if "login_session_data" in request.session:
        data = VendorProduct.objects.get(id=prod_id)
        data.delete()
        return HttpResponseRedirect(reverse('view_products'))
    else:
        return HttpResponseRedirect(reverse('login-view'))


def view_product(request, prod_id):
    if "login_session_data" in request.session:
        prod_obj = VendorProduct.objects.get(id=prod_id)
        isFarmer = RegisterModel.objects.get(email=request.session["login_session_data"]["email"])
        vendor_obj = VendorManager.objects.get(user=prod_obj.user_id)
        data_dict = {
            "product_name": prod_obj.product_name,
            "category": prod_obj.category,
            "description": prod_obj.description,
            "price": float("{:.2f}".format(prod_obj.price)),
            "image": prod_obj.image,
            "company_name": vendor_obj.company_name,
            "location": vendor_obj.location,
            "market_name": vendor_obj.market_name,
            "address": vendor_obj.address,
            "first_name": request.session["login_session_data"]["first_name"],
            "is_farmer": isFarmer.is_farmer
        }
        add_product_view_count(prod_id)
        return render(request, 'products/View_Product.html', data_dict)
    else:
        return HttpResponseRedirect(reverse('login-view'))


def dashboard(request):
    if "login_session_data" in request.session:
        login_data = request.session["login_session_data"]
        return render(request, 'home/Farmer_Dashboard.html', {"first_name": login_data["first_name"]})
    else:
        return HttpResponseRedirect(reverse('login-view'))


@api_view(["GET", "POST"])
def add_inventory(request):
    if request.method == "GET":
        if "login_session_data" in request.session:
            return render(request, 'inventory/Add_Inventory.html',
                          {"first_name": request.session["login_session_data"]["first_name"]})
        else:
            return HttpResponseRedirect(reverse('login-view'))
    if request.method == "POST":
        if "login_session_data" in request.session:
            data = request.data
            login_data = request.session["login_session_data"]
            a = VendorInventory(user_id=RegisterModel.objects.get(id=login_data["id"]),
                                item_name=data['item_name'],
                                category=data['category'],
                                description=data['description'],
                                quantity=data['quantity'],
                                unit=data['unit'])
            a.save()
            return HttpResponseRedirect(reverse('view-inventory'))


@api_view(["GET", "POST"])
def view_inventory(request):
    if request.method == "GET":
        if "login_session_data" in request.session:
            login_data = request.session["login_session_data"]
            data = VendorInventory.objects.filter(user_id=login_data["id"])
            data_list = [
                {"id": x.id,
                 "item_name": x.item_name,
                 "category": x.category,
                 "description": x.description,
                 "quantity": float("{:.2f}".format(x.quantity)),
                 "unit": x.unit}
                for x in data
            ]
            return render(request, 'inventory/View_Inventory_Page.html',
                          {"data": data_list, "first_name": request.session["login_session_data"]["first_name"]})
        else:
            return HttpResponseRedirect(reverse('login-view'))


def delete_inventory(request, in_id):
    if request.method == "GET":
        if "login_session_data" in request.session:
            data = VendorInventory.objects.get(id=in_id)
            data.delete()
            return HttpResponseRedirect(reverse('view-inventory'))
        else:
            return HttpResponseRedirect(reverse('login-view'))


@api_view(["GET", "POST"])
def edit_inventory(request, in_id):
    if request.method == "GET":
        if "login_session_data" in request.session:
            data = VendorInventory.objects.get(id=in_id)
            data_dict = {"id": data.id,
                         "item_name": data.item_name,
                         "category": data.category,
                         "description": data.description,
                         "quantity": float("{:.2f}".format(data.quantity)),
                         "unit": data.unit,
                         "first_name": request.session["login_session_data"]["first_name"]}
            return render(request, 'inventory/Edit_Inventory.html', data_dict)
        else:
            return HttpResponseRedirect(reverse('login-view'))
    if request.method == "POST":
        if "login_session_data" in request.session:
            data = request.data
            obj = VendorInventory.objects.get(id=in_id)
            obj.item_name = data['item_name']
            obj.category = data['category']
            obj.description = data['description']
            obj.quantity = data['quantity']
            obj.unit = data['unit']
            obj.save()
            return HttpResponseRedirect(reverse('view-inventory'))


def show_category(request, cat):
    if "login_session_data" in request.session:
        isFarmer = RegisterModel.objects.get(email=request.session["login_session_data"]["email"])
        data = VendorProduct.objects.filter(category=cat)
        data_list = [{
            "id": prod.id,
            "product_name": prod.product_name,
            "category": prod.category,
            "description": prod.description,
            "price": float("{:.2f}".format(prod.price)),
            "image": prod.image
        } for prod in data]
        return render(request, 'home/Get_Category.html',
                      {"products": data_list, "first_name": isFarmer.first_name, "is_farmer": isFarmer.is_farmer})
    else:
        return HttpResponseRedirect(reverse('login-view'))


def logout_session(request):
    if "login_session_data" in request.session:
        del request.session["login_session_data"]
        return HttpResponseRedirect(reverse('login-view'))
    else:
        return HttpResponseRedirect(reverse('login-view'))


@api_view(["POST"])
def search_api(request):
    if "login_session_data" in request.session:
        data = request.data
        return HttpResponseRedirect("/search/" + data["search_query"])
    else:
        return HttpResponseRedirect(reverse('login-view'))


def search_view(request, search_term):
    if "login_session_data" in request.session:
        isFarmer = RegisterModel.objects.get(email=request.session["login_session_data"]["email"])
        data_list = []
        products = VendorProduct.objects.all()
        for prod in products:
            if fuzz.ratio(prod.product_name, search_term) > 60:
                data_dict = make_data_dict(prod)
                data_list.append(data_dict)
            elif fuzz.ratio(prod.category, search_term) > 60:
                data_dict = make_data_dict(prod)
                data_list.append(data_dict)
            elif fuzz.ratio(prod.description, search_term) > 60:
                data_dict = make_data_dict(prod)
                data_list.append(data_dict)

        if not data_list:
            vendors = VendorManager.objects.all()
            for ven in vendors:
                if fuzz.ratio(ven.company_name.lower(), search_term.lower()) > 60:
                    ven_products = VendorProduct.objects.filter(user_id=ven.user)
                    for ven_prods in ven_products:
                        data_dict = make_data_dict(ven_prods)
                        data_list.append(data_dict)
                elif fuzz.ratio(ven.location.lower(), search_term.lower()) > 60:
                    ven_products = VendorProduct.objects.filter(user_id=ven.user)
                    for ven_prods in ven_products:
                        data_dict = make_data_dict(ven_prods)
                        data_list.append(data_dict)
                elif fuzz.ratio(ven.market_name.lower(), search_term.lower()) > 60:
                    ven_products = VendorProduct.objects.filter(user_id=ven.user)
                    for ven_prods in ven_products:
                        data_dict = make_data_dict(ven_prods)
                        data_list.append(data_dict)
        return render(request, "home/Search.html",
                      {"products": data_list, "first_name": isFarmer.first_name, "is_farmer": isFarmer.is_farmer})
    else:
        return HttpResponseRedirect(reverse('login-view'))


def product_charts(request):
    if "login_session_data" in request.session:
        reg_obj = RegisterModel.objects.get(email=request.session["login_session_data"]["email"])
        data_list_global = []
        data_list_user = []
        data_product_views = []
        data_cost_list = []
        category_list = ["vegetables", "fruits", "dairy", "livestock", "honey", "seasonalfoods"]
        for category in category_list:
            products_obj = VendorProduct.objects.filter(category=category)
            data_list_global.append({"category": category.title(), "value": len(products_obj)})

        for category in category_list:
            products_obj = VendorProduct.objects.filter(category=category, user_id=reg_obj)
            data_list_user.append({"category": category.title(), "value": len(products_obj)})

        users = RegisterModel.objects.filter(is_farmer=False).count()
        farmers = RegisterModel.objects.filter(is_farmer=True).count()

        views_obj = ProductViews.objects.all()
        for prod in views_obj:
            product = VendorProduct.objects.get(id=prod.product.id)
            data_product_views.append({"product_name": product.product_name, "views": prod.views})
        newlist = sorted(data_product_views, key=lambda d: d['views'], reverse=True)
        newlist = newlist[0:5]

        cost_cats = ["raw materials", "Equipment", "vehicles", "labour"]
        for costcat in cost_cats:
            cost_data = CostManager.objects.filter(vendor=reg_obj, category=costcat)
            sum = 0
            for c in cost_data:
                sum = sum + c.expense
            data_cost_list.append({"category": costcat, "total_exp": float("{:.3f}".format(sum))})
        return render(request, "analytics/Charts.html",
                      {"data_global": data_list_global, "data_user": data_list_user, "users": users,
                       "farmers": farmers, "product_trends": newlist, "cost_list": data_cost_list,
                       "first_name": request.session["login_session_data"]["first_name"]})
    else:
        return HttpResponseRedirect(reverse('login-view'))


def add_product_view_count(prod_id):
    product_count = ProductViews.objects.filter(product=VendorProduct.objects.get(id=prod_id)).count()
    if product_count == 0:
        prod_instance = ProductViews(product=VendorProduct.objects.get(id=prod_id), views=1)
        prod_instance.save()
    else:
        prod_instance = ProductViews.objects.get(product=VendorProduct.objects.get(id=prod_id))
        prod_instance.views = prod_instance.views + 1
        prod_instance.save()
    return True


@api_view(["POST", "GET"])
def publish_blog(request):
    if request.method == "GET":
        if "login_session_data" in request.session:
            return render(request, 'blog/Publish_Article.html',
                          {"first_name": request.session["login_session_data"]["first_name"]})
        else:
            return HttpResponseRedirect(reverse('login-view'))
    if request.method == "POST":
        if "login_session_data" in request.session:
            data = request.data
            obj = VendorBlogs(vendor=RegisterModel.objects.get(email=request.session["login_session_data"]["email"]),
                              title=data["title"],
                              content=str(data["content"]))
            obj.save()
            return HttpResponseRedirect(reverse('view-blogs'))


def view_blogs(request):
    if "login_session_data" in request.session:
        login_data = request.session["login_session_data"]
        data = VendorBlogs.objects.filter(vendor=login_data["id"])
        blog_list = [{"id": i.id, "title": i.title, "date_published": i.date_created.strftime("%d-%B-%Y | %H-%M %p"),
                      "last_updated": i.date_updated.strftime("%d-%B-%Y | %H-%M %p")} for i
                     in data]
        return render(request, "blog/View_Blogs.html",
                      {"data": blog_list, "first_name": request.session["login_session_data"]["first_name"]})
    else:
        return HttpResponseRedirect(reverse('login-view'))


@api_view(["GET", "POST"])
def edit_blog(request, blog_id):
    if "login_session_data" in request.session:
        if request.method == "GET":
            data = VendorBlogs.objects.get(id=blog_id)
            data_dict = {"id": data.id, "title": data.title, "content": data.content}
            return render(request, 'blog/Edit_Blog.html', data_dict)
        if request.method == "POST":
            data = request.data
            data_obj = VendorBlogs.objects.get(id=blog_id)
            data_obj.title = data["title"]
            data_obj.content = data["content"]
            data_obj.save()
            return HttpResponseRedirect(reverse('view-blogs'))
    else:
        return HttpResponseRedirect(reverse('login-view'))


def delete_blog(request, blog_id):
    if "login_session_data" in request.session:
        data = VendorBlogs.objects.get(id=blog_id)
        data.delete()
        return HttpResponseRedirect(reverse('view-blogs'))
    else:
        return HttpResponseRedirect(reverse('login-view'))


@api_view(["GET", "POST"])
def cost_manager_view(request):
    if "login_session_data" in request.session:
        if request.method == "GET":
            return render(request, 'cost/Cost_Management.html',
                          {"first_name": request.session["login_session_data"]["first_name"]})
        if request.method == "POST":
            data = request.data
            cost_obj = CostManager(
                vendor=RegisterModel.objects.get(email=request.session["login_session_data"]["email"]),
                category=data["category"],
                coster=data["coster"],
                expense=data["expense"])
            cost_obj.save()
            return HttpResponseRedirect(reverse('view-expenses'))
    else:
        return HttpResponseRedirect(reverse('login-view'))


def view_expenses(request):
    if "login_session_data" in request.session:
        login_data = request.session["login_session_data"]
        data_obj = CostManager.objects.filter(vendor=login_data["id"])
        exp_list = [
            {"id": i.id, "coster": i.coster, "category": i.category, "expense": float("{:.2f}".format(i.expense)),
             "date_created": i.date_created.strftime("%d-%B-%Y | %H-%M %p")} for i in data_obj]
        return render(request, 'cost/View_Expenses.html',
                      {"data": exp_list, "first_name": request.session["login_session_data"]["first_name"]})
    else:
        return HttpResponseRedirect(reverse('login-view'))


@api_view(["GET", "POST"])
def edit_expenses(request, exp_id):
    if "login_session_data" in request.session:
        if request.method == "GET":
            data_obj = CostManager.objects.get(id=exp_id)
            data_dict = {"id": data_obj.id, "coster": data_obj.coster, "category": data_obj.category,
                         "expense": float("{:.3f}".format(data_obj.expense)),
                         "first_name": request.session["login_session_data"]["first_name"]}
            return render(request, 'cost/Edit_Cost.html', data_dict)
        if request.method == "POST":
            data = request.data
            cost_obj = CostManager.objects.get(id=exp_id)
            cost_obj.coster = data["coster"]
            cost_obj.category = data["category"]
            cost_obj.expense = data["expense"]
            cost_obj.save()
            return HttpResponseRedirect(reverse('view-expenses'))
    else:
        return HttpResponseRedirect(reverse('login-view'))


def delete_expense(request, exp_id):
    if "login_session_data" in request.session:
        if request.method == "GET":
            data_obj = CostManager.objects.get(id=exp_id)
            data_obj.delete()
            return HttpResponseRedirect(reverse('view-expenses'))
    else:
        return HttpResponseRedirect(reverse('login-view'))


def view_blog_list(request):
    if "login_session_data" in request.session:
        blogs = VendorBlogs.objects.all()
        login_data = request.session["login_session_data"]
        isFarmer = RegisterModel.objects.get(id=login_data["id"])
        isFarmer = isFarmer.is_farmer
        data_list = []
        for i in blogs:
            data_list.append({
                "author": i.vendor.first_name + " " + i.vendor.last_name,
                "title": i.title,
                "id": i.id,
                "date_published": i.date_created.strftime("%d-%B-%Y")
            })
        return render(request, 'blog/List_Blogs.html', {"data": data_list, "is_farmer": isFarmer,
                                                        "first_name": request.session["login_session_data"][
                                                            "first_name"]})
    else:
        return HttpResponseRedirect(reverse('login-view'))


def show_blog(request, blog_id):
    if "login_session_data" in request.session:
        login_data = request.session["login_session_data"]
        isFarmer = RegisterModel.objects.get(id=login_data["id"])
        isFarmer = isFarmer.is_farmer
        blog = VendorBlogs.objects.get(id=int(blog_id))
        data = {
            "author": blog.vendor.first_name + " " + blog.vendor.last_name,
            "title": blog.title,
            "id": blog.id,
            "date_published": blog.date_created.strftime("%d-%B-%Y"),
            "content": blog.content,
            "is_farmer": isFarmer,
            "first_name": request.session["login_session_data"]["first_name"]
        }
        return render(request, 'blog/Show_Blog.html', data)
    else:
        return HttpResponseRedirect(reverse('login-view'))


def about_team(request):
    return render(request, 'landing/index.html')
