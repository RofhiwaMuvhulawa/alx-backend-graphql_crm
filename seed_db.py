import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order
from decimal import Decimal

def seed_database():
    # Create sample customers
    customers = [
        Customer.objects.create(name="John Doe", email="john@example.com", phone="+1234567890"),
        Customer.objects.create(name="Jane Smith", email="jane@example.com", phone="123-456-7890"),
        Customer.objects.create(name="Bob Johnson", email="bob@example.com"),
    ]
    
    # Create sample products
    products = [
        Product.objects.create(name="Laptop", price=Decimal('999.99'), stock=10),
        Product.objects.create(name="Mouse", price=Decimal('29.99'), stock=50),
        Product.objects.create(name="Keyboard", price=Decimal('79.99'), stock=25),
    ]
    
    # Create sample orders
    order1 = Order.objects.create(
        customer=customers[0],
        total_amount=Decimal('1029.98')
    )
    order1.products.set([products[0], products[1]])
    
    order2 = Order.objects.create(
        customer=customers[1],
        total_amount=Decimal('109.98')
    )
    order2.products.set([products[1], products[2]])
    
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()