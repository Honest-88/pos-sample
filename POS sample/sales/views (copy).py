from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django_pos.wsgi import *
from django_pos import settings
from django.template.loader import get_template
from customers.models import Customer
from products.models import Product
from weasyprint import HTML, CSS
from .models import Sale, SaleDetail
import json


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@login_required(login_url="/accounts/login/")
def SalesListView(request):
    context = {
        "active_icon": "sales",
        "sales": Sale.objects.all()
    }
    return render(request, "sales/sales.html", context=context)


@login_required(login_url="/accounts/login/")
def SalesAddView(request):
    context = {
        "active_icon": "sales",
        "customers": [c.to_select2() for c in Customer.objects.all()]
    }

    if request.method == 'POST':
        if is_ajax(request=request):
            # Save the POST arguements
            data = json.load(request)

            # Extract values from the data
            customer_id = int(data['customer'])
            sub_total = float(data["sub_total"])
            tax_percentage = float(data["tax_percentage"])
            amount_payed = float(data["amount_payed"])

            # Calculate tax amount
            tax_amount = sub_total * (tax_percentage / 100)

            # Calculate grand total including tax
            grand_total = sub_total + tax_amount

            # Calculate the change amount
            amount_change = amount_payed - grand_total

            sale_attributes = {
                "customer": Customer.objects.get(id=customer_id),
                "sub_total": sub_total,
                "grand_total": grand_total,
                "tax_amount": tax_amount,
                "tax_percentage": tax_percentage,
                "amount_payed": amount_payed,
                "amount_change": amount_change,
            }
            
            try:
                # Create the sale
                new_sale = Sale.objects.create(**sale_attributes) 
                #print("Sale created: ", new_sale.id)              
                # Create the sale details
                products = data["products"]
                #print("Products: ", products)

                for product in products:
                    detail_attributes = {
                        "sale": new_sale,
                        "product": Product.objects.get(id=int(product["id"])),
                        "price": product["price"],
                        "quantity": product["quantity"],
                        "total_detail": product["total_product"],
                        "buying_price": product["buying_price"]  # Add buying_price field
                    }
                    sale_detail_new = SaleDetail.objects.create(
                        **detail_attributes)

                    # Update the product quantity and total amount
                    product_obj = Product.objects.get(id=int(product["id"]))              
                    product_obj.quantity -= int(product["quantity"])
                    product_obj.total_amount -= float(product["total_product"])
                    product_obj.save()
   
                # Update the grand product total
                grand_product_total = sum([float(p["total_product"]) for p in products])
                product_application = Application.objects.get(name="product")
                product_application.grand_product_total -= grand_product_total
                product_application.save()

                # Update the grand total amount
                sales_application = Application.objects.get(name="sales")
                sales_application.grand_total_amount += grand_total
                sales_application.save()

                # Call update_totals() method on the sale instance
                new_sale.update_totals()
                
                messages.success(
                    request, 'Sale created succesfully!', extra_tags="success")
            
            except Exception as e:
                messages.error(request, 'There was an error during the creation!', extra_tags="danger")
                #print("Error creating sale: ", str(e))
        return redirect('sales:sales_list')

    return render(request, "sales/sales_add.html", context=context)


@login_required(login_url="/accounts/login/")
def SalesDetailsView(request, sale_id):
    """
    Args:
        sale_id: ID of the sale to view
    """
    try:
        # Get tthe sale
        sale = Sale.objects.get(id=sale_id)

        # Get the sale details
        details = SaleDetail.objects.filter(sale=sale)

        context = {
            "active_icon": "sales",
            "sale": sale,
            "details": details,
        }
        return render(request, "sales/sales_details.html", context=context)
    except Exception as e:
        messages.success(
            request, 'There was an error getting the sale!', extra_tags="danger")
        print(e)
        return redirect('sales:sales_list')


@login_required(login_url="/accounts/login/")
def ReceiptPDFView(request, sale_id):
    """
    Args:
        sale_id: ID of the sale to view the receipt
    """
    # Get tthe sale
    sale = Sale.objects.get(id=sale_id)

    # Get the sale details
    details = SaleDetail.objects.filter(sale=sale)

    template = get_template("sales/sales_receipt_pdf.html")
    context = {
        "sale": sale,
        "details": details
    }
    html_template = template.render(context)

    # CSS Boostrap
    css_url = os.path.join(
        settings.BASE_DIR, 'static/css/receipt_pdf/bootstrap.min.css')

    # Create the pdf
    pdf = HTML(string=html_template).write_pdf(stylesheets=[CSS(css_url)])

    return HttpResponse(pdf, content_type="application/pdf")
