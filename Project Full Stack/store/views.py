from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage # Required for AI upload
import json
import datetime

# Standard imports from your project
from .models import * from .utils import cookieCart, cartData, guestOrder

# AI Import - Make sure ai_utils.py is in the same folder!
from .ai_utils import analyze_image 

def store(request):
	data = cartData(request)
	cartItems = data['cartItems']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)

def cart(request):
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

# --- NEW: AI IMAGE SEARCH VIEW ---
def ai_search(request):
    data = cartData(request)
    cartItems = data['cartItems']
    
    if request.method == 'POST' and request.FILES.get('image_file'):
        image_file = request.FILES['image_file']
        
        # Save the uploaded file to the 'media' folder
        fs = FileSystemStorage()
        filename = fs.save(image_file.name, image_file)
        file_path = fs.path(filename)
        file_url = fs.url(filename)

        # Run the AI Computer Vision Model
        try:
            label = analyze_image(file_path)
            # Find products in database that match the AI label
            suggested_products = Product.objects.filter(name__icontains=label)
        except Exception as e:
            label = "Analysis Error"
            suggested_products = []
            print(f"AI Error: {e}")

        context = {
            'label': label, 
            'image_url': file_url, 
            'cartItems': cartItems,
            'suggested_products': suggested_products
        }
        return render(request, 'store/ai_results.html', context)

    context = {'cartItems': cartItems}
    return render(request, 'store/ai_upload.html', context)

# --- STANDARD E-COMMERCE LOGIC CONTINUED ---

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)
	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()
	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)