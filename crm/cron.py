import os
from datetime import datetime
from django.conf import settings

def log_crm_heartbeat():
    """Log a heartbeat message to confirm CRM application health"""
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    message = f"{timestamp} CRM is alive\n"
    
    # Append to heartbeat log file
    with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
        log_file.write(message)
    
    # Optional: Test GraphQL endpoint responsiveness
    try:
        from graphene_django.views import GraphQLView
        from django.test import RequestFactory
        from alx_backend_graphql_crm.schema import schema
        
        # Simple test query
        factory = RequestFactory()
        request = factory.post('/graphql', {
            'query': '{ hello }'
        })
        
        # Execute hello query to test GraphQL endpoint
        result = schema.execute('{ hello }')
        if result.data and result.data.get('hello'):
            with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
                log_file.write(f"{timestamp} GraphQL endpoint responsive: {result.data['hello']}\n")
    except Exception as e:
        with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
            log_file.write(f"{timestamp} GraphQL endpoint test failed: {str(e)}\n")


def update_low_stock():
    """Execute UpdateLowStockProducts mutation and log results"""
    import requests
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        # GraphQL mutation query
        mutation_query = """
        mutation {
            updateLowStockProducts {
                updatedProducts {
                    id
                    name
                    stock
                }
                message
                success
                count
            }
        }
        """
        
        # Execute mutation via GraphQL endpoint
        response = requests.post(
            'http://localhost:8000/graphql/',
            json={'query': mutation_query},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {}).get('updateLowStockProducts', {})
            
            if data.get('success'):
                updated_products = data.get('updatedProducts', [])
                count = data.get('count', 0)
                message = data.get('message', '')
                
                # Log successful update
                log_message = f"{timestamp} Low stock update successful: {message}\n"
                
                if updated_products:
                    log_message += f"{timestamp} Updated products:\n"
                    for product in updated_products:
                        log_message += f"{timestamp}   - {product['name']}: New stock level {product['stock']}\n"
                else:
                    log_message += f"{timestamp} No products needed restocking\n"
                    
                with open('/tmp/low_stock_updates_log.txt', 'a') as log_file:
                    log_file.write(log_message)
            else:
                # Log mutation failure
                error_message = data.get('message', 'Unknown error')
                with open('/tmp/low_stock_updates_log.txt', 'a') as log_file:
                    log_file.write(f"{timestamp} Low stock update failed: {error_message}\n")
        else:
            # Log HTTP error
            with open('/tmp/low_stock_updates_log.txt', 'a') as log_file:
                log_file.write(f"{timestamp} HTTP error {response.status_code}: {response.text}\n")
                
    except Exception as e:
        # Log exception
        with open('/tmp/low_stock_updates_log.txt', 'a') as log_file:
            log_file.write(f"{timestamp} Exception during low stock update: {str(e)}\n")