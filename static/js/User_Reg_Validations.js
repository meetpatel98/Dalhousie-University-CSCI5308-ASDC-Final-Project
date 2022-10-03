const form = document.getElementById('form');
const firstname = document.getElementById('firstname');
const lastname = document.getElementById('lastname');
const dateOfBirth = document.getElementById('dateOfBirth');
const phoneNumber = document.getElementById('phonenumber');
const email = document.getElementById('email');
const password = document.getElementById('password');
const password2 = document.getElementById('password2');

form.addEventListener('submit', e => {
	e.preventDefault();
	checkInputs();
});


function checkInputs() {
	// trim to remove the whitespaces
	const firstnameValue = firstname.value.trim();
    const lastnameValue = lastname.value.trim();
	var dateOfBirthValue = dateOfBirth.value;
	const phoneNumberValue = phoneNumber.value.trim();
	const emailValue = email.value.trim();
	const passwordValue = password.value.trim();
	const password2Value = password2.value.trim();
	var phoneRegex = /^\d{10}$/;

	const firstnameLength = firstname.value.length;
	const lastnameLength = lastname.value.length;

	const passwordLength = password.value.length;
	const password2Length = password2.value.length;


	var today = new Date();
	var dd = String(today.getDate()).padStart(2, '0');
	var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
	var yyyy = today.getFullYear();
	today = yyyy + '-' + mm + '-' + dd;
	
	if(firstnameValue === '') {
		setErrorFor(firstname, 'First Name cannot be blank');
	} else if ( firstnameLength == 1 || firstnameLength > 50) {
		setErrorFor(firstname, 'Enter valid First name having characters greater than 2 and less than 50');
	}
	else {
		setSuccessFor(firstname);
	}

	if(lastnameValue === '') {
		setErrorFor(lastname, 'Last Name cannot be blank');
	} else if ( lastnameLength == 1 || lastnameLength > 50) {
		setErrorFor(lastname, 'Enter valid Last name having characters greater than 2 and less than 50');
	}
	else {
		setSuccessFor(lastname);
	}

	if(dateOfBirthValue === ''){
		setErrorFor(dateOfBirth, 'Date of Birth cannot be blank');
	} else if (dateOfBirthValue > today) {
		setErrorFor(dateOfBirth, 'Enter valid date');
	} else {
		setSuccessFor(dateOfBirth);
	}

	if(emailValue === '') {
		setErrorFor(email, 'Email cannot be blank');
	} else if (!isEmail(emailValue)) {
		setErrorFor(email, 'Not a valid email');
	} else {
		setSuccessFor(email);
	}

	if(phoneNumberValue === ''){
		setErrorFor(phoneNumber, 'Phone Number cannot be blank');
	} else {
		setSuccessFor(phoneNumber);
	}

	if(!phoneNumberValue.match(phoneRegex)){
		setErrorFor(phoneNumber, 'Enter Valid Phone Number');
	} else {
		setSuccessFor(phoneNumber);
	}

	if(passwordValue === '') {
		setErrorFor(password, 'Password cannot be blank');
	} else if (passwordLength < 8){
		setErrorFor(password, 'Password must be atleast 8 character long')
	} else {
		setSuccessFor(password);
	}
	
	if(password2Value === '') {
		setErrorFor(password2, 'Password2 cannot be blank');
	} else if(passwordValue !== password2Value) {
		setErrorFor(password2, 'Passwords does not match');
	} else if (password2Length < 8){
		setErrorFor(password2, 'Password must be atleast 8 character long')
	} else{
		setSuccessFor(password2);
	}
}

function setErrorFor(input, message) {
	const formControl = input.parentElement;
	const small = formControl.querySelector('small');
	formControl.className = 'form-control error';
	small.innerText = message;
}

function setSuccessFor(input) {
	const formControl = input.parentElement;
	formControl.className = 'form-control success';
}
	
function isEmail(email) {
	return /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(email);
}