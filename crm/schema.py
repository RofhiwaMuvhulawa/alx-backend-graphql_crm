import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
import re
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter

# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"
        filter_fields = {
            'name': ['icontains'],
            'email': ['icontains'],
            'created_at': ['gte', 'lte'],
        }
        interfaces = (graphene.relay.Node,)

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"
        filter_fields = {
            'name': ['icontains'],
            'price': ['gte', 'lte'],
            'stock': ['gte', 'lte', 'exact'],
        }
        interfaces = (graphene.relay.Node,)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"
        filter_fields = {
            'total_amount': ['gte', 'lte'],
            'order_date': ['gte', 'lte'],
            'customer__name': ['icontains'],
            'products__name': ['icontains'],
        }
        interfaces = (graphene.relay.Node,)

# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)  # Change this to:
    customerId = graphene.ID(required=True)   # Match the test query format
    product_ids = graphene.List(graphene.ID, required=True)  # Change this to:
    productIds = graphene.List(graphene.ID, required=True)   # Match the test query format
    order_date = graphene.DateTime()

# Mutation Classes
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()
    
    def mutate(self, info, input):
        try:
            # Validate phone format if provided
            if input.phone:
                phone_pattern = r'^\+?1?\d{9,15}$|^\d{3}-\d{3}-\d{4}$'
                if not re.match(phone_pattern, input.phone):
                    return CreateCustomer(
                        success=False,
                        message="Invalid phone format. Use +1234567890 or 123-456-7890"
                    )
            
            # Check if email already exists
            if Customer.objects.filter(email=input.email).exists():
                return CreateCustomer(
                    success=False,
                    message="Email already exists"
                )
            
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone or ""
            )
            
            return CreateCustomer(
                customer=customer,
                message="Customer created successfully",
                success=True
            )
        except Exception as e:
            return CreateCustomer(
                success=False,
                message=f"Error creating customer: {str(e)}"
            )

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)
    
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    success = graphene.Boolean()
    
    def mutate(self, info, input):
        customers = []
        errors = []
        
        with transaction.atomic():
            for i, customer_data in enumerate(input):
                try:
                    # Validate phone format if provided
                    if customer_data.phone:
                        phone_pattern = r'^\+?1?\d{9,15}$|^\d{3}-\d{3}-\d{4}$'
                        if not re.match(phone_pattern, customer_data.phone):
                            errors.append(f"Customer {i+1}: Invalid phone format")
                            continue
                    
                    # Check if email already exists
                    if Customer.objects.filter(email=customer_data.email).exists():
                        errors.append(f"Customer {i+1}: Email already exists")
                        continue
                    
                    customer = Customer.objects.create(
                        name=customer_data.name,
                        email=customer_data.email,
                        phone=customer_data.phone or ""
                    )
                    customers.append(customer)
                    
                except Exception as e:
                    errors.append(f"Customer {i+1}: {str(e)}")
        
        return BulkCreateCustomers(
            customers=customers,
            errors=errors,
            success=len(customers) > 0
        )

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    message = graphene.String()
    success = graphene.Boolean()
    
    def mutate(self, info, input):
        try:
            # Validate price is positive
            if input.price <= 0:
                return CreateProduct(
                    success=False,
                    message="Price must be positive"
                )
            
            # Validate stock is not negative
            stock = input.stock if input.stock is not None else 0
            if stock < 0:
                return CreateProduct(
                    success=False,
                    message="Stock cannot be negative"
                )
            
            product = Product.objects.create(
                name=input.name,
                price=input.price,
                stock=stock
            )
            
            return CreateProduct(
                product=product,
                message="Product created successfully",
                success=True
            )
        except Exception as e:
            return CreateProduct(
                success=False,
                message=f"Error creating product: {str(e)}"
            )

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderType)
    message = graphene.String()
    success = graphene.Boolean()
    
    def mutate(self, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customerId)  # Updated field name
            except Customer.DoesNotExist:
                return CreateOrder(
                    success=False,
                    message="Invalid customer ID"
                )
            
            # Validate at least one product is selected
            if not input.productIds:  # Updated field name
                return CreateOrder(
                    success=False,
                    message="At least one product must be selected"
                )
            
            # Validate all product IDs exist
            products = []
            total_amount = Decimal('0.00')
            
            for product_id in input.productIds:  # Updated field name
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                    total_amount += product.price
                except Product.DoesNotExist:
                    return CreateOrder(
                        success=False,
                        message=f"Invalid product ID: {product_id}"
                    )
            
            # Create order
            order = Order.objects.create(
                customer=customer,
                total_amount=total_amount,
                order_date=input.order_date
            )
            
            # Associate products
            order.products.set(products)
            
            return CreateOrder(
                order=order,
                message="Order created successfully",
                success=True
            )
        except Exception as e:
            return CreateOrder(
                success=False,
                message=f"Error creating order: {str(e)}"
            )

# Updated Query Class with Filtering
class Query(graphene.ObjectType):
    hello = graphene.String()
    
    # Original simple queries
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)
    
    # New filtered queries with connection fields
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
        order_by=graphene.List(graphene.String)
    )
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
        order_by=graphene.List(graphene.String)
    )
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
        order_by=graphene.List(graphene.String)
    )
    
    def resolve_hello(self, info):
        return "Hello, GraphQL!"
    
    def resolve_customers(self, info):
        return Customer.objects.all()
    
    def resolve_products(self, info):
        return Product.objects.all()
    
    def resolve_orders(self, info):
        return Order.objects.all()
    
    def resolve_all_customers(self, info, **kwargs):
        order_by = kwargs.get('order_by', [])
        queryset = Customer.objects.all()
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset
    
    def resolve_all_products(self, info, **kwargs):
        order_by = kwargs.get('order_by', [])
        queryset = Product.objects.all()
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset
    
    def resolve_all_orders(self, info, **kwargs):
        order_by = kwargs.get('order_by', [])
        queryset = Order.objects.all()
        if order_by:
            queryset = queryset.order_by(*order_by)
        return queryset

# Mutation Class
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()