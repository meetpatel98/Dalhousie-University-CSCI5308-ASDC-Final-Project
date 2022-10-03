const password = document.getElementById('password');
const password2 = document.getElementById('password2');

form.addEventListener('submit', e => {
	e.preventDefault();
	checkInputs();
});


function checkInputs() {
	
	const passwordValue = password.value.trim();
	const password2Value = password2.value.trim();

	const passwordLength = password.value.length;
	const password2Length = password2.value.length;

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
		setErrorFor(password2, 'Password must atleast be 8 character long')
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