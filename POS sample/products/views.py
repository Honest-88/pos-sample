from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Category, Product
from django.db.models import F, Sum


@login_required(login_url="/accounts/login/")
def CategoriesListView(request):
    context = {
        "active_icon": "products_categories",
        "categories": Category.objects.all()
    }
    return render(request, "products/categories.html", context=context)


@login_required(login_url="/accounts/login/")
def CategoriesAddView(request):
    context = {
        "active_icon": "products_categories",
        "category_status": Category.status.field.choices
    }

    if request.method == 'POST':
        # Save the POST arguements
        data = request.POST

        attributes = {
            "name": data['name'],
            "status": data['state'],
            "description": data['description']
        }

        # Check if a category with the same attributes exists
        if Category.objects.filter(**attributes).exists():
            messages.error(request, 'Category already exists!',
                           extra_tags="warning")
            return redirect('products:categories_add')

        try:
            # Create the category
            new_category = Category.objects.create(**attributes)

            # If it doesn't exists save it
            new_category.save()

            messages.success(request, 'Category: ' +
                             attributes["name"] + ' created succesfully!', extra_tags="success")
            return redirect('products:categories_list')
        except Exception as e:
            messages.success(
                request, 'There was an error during the creation!', extra_tags="danger")
            print(e)
            return redirect('products:categories_add')

    return render(request, "products/categories_add.html", context=context)


@login_required(login_url="/accounts/login/")
def CategoriesUpdateView(request, category_id):
    """
    Args:
        category_id : The category's ID that will be updated
    """

    # Get the category
    try:
        # Get the category to update
        category = Category.objects.get(id=category_id)
    except Exception as e:
        messages.success(
            request, 'There was an error trying to get the category!', extra_tags="danger")
        print(e)
        return redirect('products:categories_list')

    context = {
        "active_icon": "products_categories",
        "category_status": Category.status.field.choices,
        "category": category
    }

    if request.method == 'POST':
        try:
            # Save the POST arguements
            data = request.POST

            attributes = {
                "name": data['name'],
                "status": data['state'],
                "description": data['description']
            }

            # Check if a category with the same attributes exists
            if Category.objects.filter(**attributes).exists():
                messages.error(request, 'Category already exists!',
                               extra_tags="warning")
                return redirect('products:categories_add')

            # Get the category to update
            category = Category.objects.filter(
                id=category_id).update(**attributes)

            category = Category.objects.get(id=category_id)

            messages.success(request, '¡Category: ' + category.name +
                             ' updated successfully!', extra_tags="success")
            return redirect('products:categories_list')
        except Exception as e:
            messages.success(
                request, 'There was an error during the elimination!', extra_tags="danger")
            print(e)
            return redirect('products:categories_list')

    return render(request, "products/categories_update.html", context=context)


@login_required(login_url="/accounts/login/")
def CategoriesDeleteView(request, category_id):
    """
    Args:
        category_id : The category's ID that will be deleted
    """
    try:
        # Get the category to delete
        category = Category.objects.get(id=category_id)
        category.delete()
        messages.success(request, '¡Category: ' + category.name +
                         ' deleted!', extra_tags="success")
        return redirect('products:categories_list')
    except Exception as e:
        messages.success(
            request, 'There was an error during the elimination!', extra_tags="danger")
        print(e)
        return redirect('products:categories_list')


@login_required(login_url="/accounts/login/")
def ProductsListView(request):

     # Calculate daily profit
    today = date.today()
    start_date = today - timedelta(days=1)
    daily_profit = Product.objects.filter(date__date=today).aggregate(total_profit=Sum((F('price') - F('buying_price')) * F('quantity')))['total_profit']
    
    # Calculate weekly profit
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    weekly_profit = Product.objects.filter(date__date__range=[start_of_week, end_of_week]).aggregate(total_profit=Sum((F('price') - F('buying_price')) * F('quantity')))['total_profit']
    
    # Calculate monthly profit
    start_of_month = date(today.year, today.month, 1)
    end_of_month = date(today.year, today.month, 1) + timedelta(days=32)
    monthly_profit = Product.objects.filter(date__date__range=[start_of_month, end_of_month]).aggregate(total_profit=Sum((F('price') - F('buying_price')) * F('quantity')))['total_profit']


     # Calculate overall profit
    overall_profit = Product.objects.annotate(
        profit=(F('price') - F('buying_price')) * F('quantity')
    ).aggregate(total_profit=Sum('profit'))['total_profit']

   
    products = Product.objects.all().order_by('-date')
    grand_product_total =  grand_product_total = products.aggregate(total=Sum('quantity'))['total']
    grand_total_amount = products.aggregate(total_amount_sum=Sum('total_amount'))['total_amount_sum'] or 0

    context = {
        "active_icon": "products",
        "products": products,
        "grand_product_total": grand_product_total,
        "grand_total_amount": grand_total_amount,
        'overall_profit': overall_profit or 0 ,
        'daily_profit': daily_profit,
        'weekly_profit': weekly_profit,
        'monthly_profit': monthly_profit,

    }
    return render(request, "products/products.html", context=context)


@login_required(login_url="/accounts/login/")
def ProductsAddView(request):
    context = {
        "active_icon": "products_categories",
        "product_status": Product.status.field.choices,
        "categories": Category.objects.all().filter(status="ACTIVE"),
        
    }

    if request.method == 'POST':

        # Save the POST arguements
        data = request.POST

        attributes = {
            "name": data['name'],
            "status": data['status'],
            "description": data['description'],
            "category": Category.objects.get(id=data['category']),
            "buying_price": float(data['buying_price']),
            "price": float(data['price']),
            "quantity": int(data['quantity']),
        }

        # Calculate total_amount
        attributes['total_amount'] = attributes['price'] * attributes['quantity']

         # Calculate profit
        attributes['profit_amount'] = attributes['price'] - attributes['buying_price']

        # Check if a product with the same attributes exists
        if Product.objects.filter(**attributes).exists():
            messages.error(request, 'Product already exists!',
                           extra_tags="warning")
            return redirect('products:products_add')

        try:
            # Create the product
            new_product = Product.objects.create(**attributes)

            # Calculate and retrieve the profit value
            profit = new_product.profit
            # If it doesn't exists save it
            new_product.save()

            messages.success(request, 'Product: ' +
                             attributes["name"] + ' created succesfully! Profit:' + str(profit), extra_tags="success")
            return redirect('products:products_list')
        except Exception as e:
            messages.success(
                request, 'There was an error during the creation!', extra_tags="danger")
            print(e)
            return redirect('products:products_add')

    return render(request, "products/products_add.html", context=context)


@login_required(login_url="/accounts/login/")
def ProductsUpdateView(request, product_id):
    """
    Args:
        product_id : The product's ID that will be updated
    """

    # Get the product
    try:
        # Get the product to update
        product = Product.objects.get(id=product_id)
    except Exception as e:
        messages.success(
            request, 'There was an error trying to get the product!', extra_tags="danger")
        print(e)
        return redirect('products:products_list')

    context = {
        "active_icon": "products",
        "product_status": Product.status.field.choices,
        "product": product,
        "categories": Category.objects.all()
    }

    if request.method == 'POST':
        try:
            # Save the POST arguements
            data = request.POST

            attributes = {
                "name": data['name'],
                "status": data['status'],
                "description": data['description'],
                "category": Category.objects.get(id=data['category']),
                "buying_price": data['buying_price'],
                "price": data['price'],
                "quantity": data['quantity'],
                "total_amount": data['total_amount'],
            }

            # Check if a product with the same attributes exists
            if product.objects.filter(**attributes).exists():
                messages.error(request, 'Product already exists!',
                               extra_tags="warning")
                return redirect('products:products_add')

            # Get the product to update
            product = Product.objects.filter(
                id=product_id).update(**attributes)

            product = Product.objects.get(id=product_id)

            messages.success(request, '¡Product: ' + product.name +
                             ' updated successfully!', extra_tags="success")
            return redirect('products:products_list')
        except Exception as e:
            messages.success(
                request, 'There was an error during the update!', extra_tags="danger")
            print(e)
            return redirect('products:products_list')

    return render(request, "products/products_update.html", context=context)


@login_required(login_url="/accounts/login/")
def ProductsDeleteView(request, product_id):
    """
    Args:
        product_id : The product's ID that will be deleted
    """
    try:
        # Get the product to delete
        product = Product.objects.get(id=product_id)
        product.delete()
        messages.success(request, '¡Product: ' + product.name +
                         ' deleted!', extra_tags="success")
        return redirect('products:products_list')
    except Exception as e:
        messages.success(
            request, 'There was an error during the elimination!', extra_tags="danger")
        print(e)
        return redirect('products:products_list')


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@login_required(login_url="/accounts/login/")
def GetProductsAJAXView(request):
    if request.method == 'POST':
        if is_ajax(request=request):
            data = []

            products = Product.objects.filter(
                name__icontains=request.POST['term'])
            for product in products[0:10]:
                item = product.to_json()
                data.append(item)

            return JsonResponse(data, safe=False)
