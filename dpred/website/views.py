import re
from django.shortcuts import render, redirect, HttpResponse
# from django.http import HttpResponse
from django.contrib import messages, auth
from django.contrib.auth.models import User
from .models import veterinarian
from appoint.views import patientappo, docappo
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from keras.models import load_model  # TensorFlow is required for Keras to work
from PIL import Image, ImageOps  # Install pillow instead of PIL
import numpy as np
# from website.model import keras_model
# Create your views here.


def home(request):
    return render(request, 'index.html', {})


# def loginn(request):
#     # if 'username' in request.session:
#     #     username = request.session['username']
#     #     return render(request, 'userprofile.html', {'username': username})
#     if request.method == "POST":
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(username=username, password=password)

#         if user is not None:
#             request.session['username'] = username
#             login(request, user)
#             return redirect(request, "userprofile", {'username': username})
#         else:
#             messages.error(request, "Inavlid User or Password")
#             return redirect(request, "login.html")

#     return render(request, "login.html", {})

def loginn(request):
    if 'vetusername' in request.session:
        messages.error(
            request, "Cannot Login as User When You Are Veterinarian")
        return redirect("home")
    if 'username' in request.session:
        if 'id' in request.session:
            username = request.session.get('username')
            return render(request, 'userprofile.html', {'username': username})
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            request.session['username'] = username
            user_id = request.user.id
            request.session['id'] = user_id
            # Redirect to userprofile view upon successful login
            return redirect('userprofile')
        else:
            messages.error(request, "Invalid User or Password")
            return redirect('login')  # Redirect to login view if login fails

    return render(request, "login.html", {})


def vetloginn(request):
    if 'username' in request.session:
        messages.error(
            request, "Cannot Login as Veterinarian When You Are User")
        return redirect("home")
    if 'vetusername' in request.session:
        if 'vet_id' in request.session:
            vetusername = request.session.get('vetusername')
            vet_id = request.session.get('vet_id')
            return render(request, 'vetprofile.html', {'vetusername': vetusername, 'vet_id': vet_id})
    if request.method == "POST":
        vetusername = request.POST['username']
        password = request.POST['password']
        try:
            user_check = veterinarian.objects.get(username=vetusername)
            if user_check is not None:
                if user_check.password == password:
                    vet_id = user_check.id
                    request.session['vetusername'] = vetusername
                    request.session['vet_id'] = vet_id
                    # messages.error(request, "user not found")
                    # if pass_check is None:
                    # messages.error(request, "Invalid Password")
                    # if user_check and pass_check is not None:
                    # if veterinarian.password == password:
                    # login(request, user_check)
                    return render(request, 'vetprofile.html', {'vetusername': vetusername, 'vet_id': vet_id})
                    # else:
                    # messages.error(request, "Invalid password")
                    # return redirect("vetlogin")
            else:
                messages.error(request, "Inavlid User and Password")
                return render(request, "vetlogin.html")
        except veterinarian.DoesNotExist:
            messages.error(request, "Invalid user")
            return render(request, "vetlogin.html")

    return render(request, "vetlogin.html", {})


def registerr(request):
    return render(request, "index.html", {})


# def signup(request):
#     if request.method == "POST":
#         username = request.POST['username']
#         email = request.POST['email']
#         password = request.POST['password']

#         myuser = User.objects.create_user(username, email, password)
#         myuser.save()

#         return redirect('login')
#     else:
#         messages.error(request, "Invalid")

#     return render(request, "index.html", {})

def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if 'username' in request.session or 'vetusername' in request.session:
            messages.error(request, "Cannot Register when You are Logged in")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('signup')

        # Create a new user
        myuser = User.objects.create_user(username, email, password)
        myuser.save()

        messages.success(
            request, "Account created successfully. Please log in.")
        return redirect('login/')
    else:
        # Redirect to a proper page or render a specific template
        return render(request, "index.html", {})


# def userprofile(request):

#     # Retrieve username from session
#     username = request.session.get('username')
#     return render(request, 'userprofile.html', {'username': username})


def userprofile(request):

    if 'username' in request.session:
        if 'id' in request.session:
            username = request.session.get('username')
        return render(request, 'userprofile.html', {'username': username})
    else:
        return redirect('login/')


def vetprofile(request):
    if 'vetusername' in request.session:
        if 'vet_id' in request.session:
            vetusername = request.session.get('vetusername')
            vet_id = request.session.get('vet_id')
        return render(request, "vetprofile.html", {'vetusername': vetusername, 'vet_id': vet_id})
    else:
        return redirect('login/')


def predict(request):
    if 'username' or 'vetusername' in request.session:
        return render(request, "predict.html", {})
    else:
        return redirect('home')


# ---------------------------------------------------------------------------


def skinpredict(request):
    if 'username' or 'vetusername' in request.session:

        final_string = None  # Initialize class_name
        confidence_score = None

        if request.method == "POST" and request.FILES['skin']:

            imagetest = request.FILES['skin']
            # Disable scientific notation for clarity
            np.set_printoptions(suppress=True)
            # Load the model
            model = load_model("./savedModels/keras_model.h5", compile=False)

            # Load the labels
            class_names = open("./savedModels/labels.txt", "r").readlines()

            # Create the array of the right shape to feed into the keras model
            # The 'length' or number of images you can put into the array is
            # determined by the first position in the shape tuple, in this case 1
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

            # Replace this with the path to your image
            image = Image.open(imagetest).convert("RGB")

            # resizing the image to be at least 224x224 and then cropping from the center
            size = (224, 224)
            image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)

            # turn the image into a numpy array
            image_array = np.asarray(image)

            # Normalize the image
            normalized_image_array = (
                image_array.astype(np.float32) / 127.5) - 1

            # Load the image into the array
            data[0] = normalized_image_array

            # Predicts the model
            prediction = model.predict(data)
            index = np.argmax(prediction)
            class_name = class_names[index]
            confidence_score = prediction[0][index]

            # Print prediction and confidence score
            print("Class:", class_name[2:], end="")
            print("Confidence Score:", confidence_score)

            # Remove numbers from the string
            string_without_numbers = re.sub(r'\d', '', class_name)

            string_without_space = string_without_numbers.replace(' ', '')

            # Replace underscores with spaces
            string_with_spaces = string_without_space.replace('_', ' ')

            # Ensure the string starts with a capital letter
            final_string = string_with_spaces.capitalize()

        return render(request, "skinpredict.html", {'prediction': final_string, 'confidence_score': confidence_score})
    else:
        return redirect('home')


def docappo(request):

    return render(request, "docappo.html", {})


# -------------------------------------------------------
def sample(request):

    if 'username' or 'vetusername' in request.session:

        class_name = None  # Initialize class_name

        if request.method == "POST" and request.FILES['skin']:

            imagetest = request.FILES['skin']
            # Disable scientific notation for clarity
            np.set_printoptions(suppress=True)
            # Load the model
            model = load_model("./savedModels/keras_model.h5", compile=False)

            # Load the labels
            class_names = open("./savedModels/labels.txt", "r").readlines()

            # Create the array of the right shape to feed into the keras model
            # The 'length' or number of images you can put into the array is
            # determined by the first position in the shape tuple, in this case 1
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)

            # Replace this with the path to your image
            image = Image.open(imagetest).convert("RGB")

            # resizing the image to be at least 224x224 and then cropping from the center
            size = (224, 224)
            image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)

            # turn the image into a numpy array
            image_array = np.asarray(image)

            # Normalize the image
            normalized_image_array = (
                image_array.astype(np.float32) / 127.5) - 1

            # Load the image into the array
            data[0] = normalized_image_array

            # Predicts the model
            prediction = model.predict(data)
            index = np.argmax(prediction)
            class_name = class_names[index]
            confidence_score = prediction[0][index]

            # Print prediction and confidence score
            print("Class:", class_name[2:], end="")
            print("Confidence Score:", confidence_score)

        return render(request, "sample.html", {'prediction': class_name})
    else:
        return redirect('home')


def user_logout(request):
    # auth.logout(request)
    if "username" or "vetusername" in request.session:
        request.session.flush()
    return redirect('home')
