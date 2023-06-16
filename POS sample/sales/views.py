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
from django.db import transaction
import json
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import os
from django.db.models import F, IntegerField, FloatField
from django.db.models.functions import Cast


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@login_required(login_url="/accounts/login/")
def SalesListView(request):
    context = {
        "active_icon": "sales",
        "sales": Sale.objects.all().order_by('-date')
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
                "customer": Customer.objects.get(id=int(data['customer'])),
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
                # Create the sale details
                products = data["products"]
              
                for product in products:
                    detail_attributes = {
                        "sale": new_sale,
                        #"sale": Sale.objects.get(id=new_sale.id),
                        "product": Product.objects.get(id=int(product["id"])),
                        "price": float(product["price"]),
                        "quantity": int(product["quantity"]),
                        "total_detail": float(product["total_product"]) * int(product["quantity"]),
                        "buying_price": float(product["buying_price"]),  # Add buying_price field
                    }

                    try:
                        sale_detail_new = SaleDetail.objects.create(**detail_attributes)
                        sale_detail_new.save()

                        # Update the product quantity and total amount
                        product_obj = Product.objects.get(id=int(product["id"]))
                        quantity_to_deduct = int(product["quantity"])
                        product_obj.quantity -= quantity_to_deduct
                        #product_obj.quantity = F('quantity', output_field=IntegerField()) - Cast(int(product["quantity"]), output_field=IntegerField())                                   
                        product_obj.total_amount -= (float(product["total_product"]) * quantity_to_deduct)                  
                        product_obj.save()

                        # Add print statements to track the changes
                        print("Product quantity:", product_obj.quantity)
                        print("Product total amount:", product_obj.total_amount)

                    except Exception as e:
                        messages.error(request, 'There was an error creating the sale detail!',
                                       extra_tags="danger")
                        print("Error creating sale detail:", str(e))
                        
                # Update the grand product total
                grand_product_total = sum([float(p["total_product"]) for p in products])
                product_application = Application.objects.get(name="product")
                product_application.grand_product_total -= grand_product_total
                product_application.save()

                # Add print statements to track the changes
                print("Grand product total:", product_application.grand_product_total)

                # Update the grand total amount
                grand_total_amount = grand_total
                sales_application = Application.objects.get(name="sales")
                sales_application.grand_total_amount += grand_total_amount
                sales_application.save()

                # Add print statements to track the changes
                print("Grand total amount:", sales_application.grand_total_amount)

                # Call update totals method on the sale instance
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
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="receipt.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    html_template = template.render(context, request=request)
    story = []

    # Add the header
    styles = getSampleStyleSheet()
    header = Paragraph("<font size='16'>Receipt</font>", style=styles['Title'])
    story.append(header)

    # Add the table of sale details
    table_data = [("Product", "Quantity", "Price")]

    for detail in details:
        table_data.append((detail.product.name, detail.quantity, detail.price))

    table = Table(table_data)
    story.append(table)

    # Add the footer
    footer = Paragraph("<font size='12'>Thank you for your purchase!</font>", style=styles['Normal'])
    story.append(footer)

    pdf = HTML(string=html_template, base_url=request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="receipt.pdf"'

    return response
