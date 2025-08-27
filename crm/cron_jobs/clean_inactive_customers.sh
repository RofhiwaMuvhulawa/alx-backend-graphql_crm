#!/bin/bash

# Navigate to the Django project directory
cd "$(dirname "$0")/../.."

# Execute Django management command to delete inactive customers
result=$(python manage.py shell -c "
from crm.models import Customer, Order
from datetime import datetime, timedelta
from django.utils import timezone

# Calculate date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders in the last year
inactive_customers = Customer.objects.exclude(
    orders__order_date__gte=one_year_ago
).distinct()

count = inactive_customers.count()
inactive_customers.delete()

print(f'Deleted {count} inactive customers')
")

# Log the result with timestamp
echo "$(date '+%d/%m/%Y-%H:%M:%S') $result" >> /tmp/customer_cleanup_log.txt