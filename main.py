# lambda_function.py

import json
import os
import unittest
from unittest.mock import MagicMock

# AWS Powertools for Python imports
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.exceptions import (
    BadRequestError,
    NotFoundError,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize Powertools utilities
# It's good practice to initialize these globally for the Lambda function.
# The service name helps identify logs, traces, and metrics in CloudWatch.
logger = Logger(service="multi-endpoint-api")

# Initialize the API Gateway REST resolver
# This resolver will handle routing requests to the correct functions based on the path and HTTP method.
app = APIGatewayRestResolver()

# --- API Endpoints ---


@app.get("/products")
def list_products():
    """
    Handles GET requests to /products.
    Returns a list of dummy product data.
    """
    logger.info("Received request to list products")
    products = [
        {"id": "prod1", "name": "Laptop", "price": 1200},
        {"id": "prod2", "name": "Mouse", "price": 25},
        {"id": "prod3", "name": "Keyboard", "price": 75},
    ]

    return {"products": products}


@app.get("/products/<product_id>")
def get_product(product_id: str):
    """
    Handles GET requests to /products/{product_id}.
    Retrieves a specific product by its ID.
    Raises NotFoundError if the product is not found.
    """
    logger.info(f"Received request to get product with ID: {product_id}")
    # Simulate a database lookup
    products_db = {
        "prod1": {"id": "prod1", "name": "Laptop", "price": 1200},
        "prod2": {"id": "prod2", "name": "Mouse", "price": 25},
        "prod3": {"id": "prod3", "name": "Keyboard", "price": 75},
    }
    product = products_db.get(product_id)
    if not product:
        logger.warning(f"Product with ID {product_id} not found.")

        raise NotFoundError(f"Product with ID '{product_id}' not found.")

    return product


@app.post("/products")
def create_product():
    """
    Handles POST requests to /products.
    Creates a new product from the request body.
    Raises BadRequestError if the request body is invalid.
    """
    logger.info("Received request to create a new product")
    try:
        body = app.current_event.json_body
        product_name = body.get("name")
        product_price = body.get("price")

        if not product_name or not isinstance(product_price, (int, float)):
            logger.error("Invalid product data provided for creation.")

            raise BadRequestError(
                "Invalid product data. 'name' and 'price' are required."
            )

        # Simulate saving to a database
        new_product_id = (
            f"prod_{len(os.urandom(4).hex())}"  # Simple unique ID generation
        )
        new_product = {
            "id": new_product_id,
            "name": product_name,
            "price": product_price,
        }
        logger.info(f"Created new product: {new_product}")

        return {
            "message": "Product created successfully",
            "product": new_product,
        }, 201  # HTTP 201 Created
    except BadRequestError as e:
        raise e  # Re-raise BadRequestError for APIGatewayRestResolver to handle
    except Exception as e:
        logger.exception("Error processing create product request.")

        raise BadRequestError(f"An unexpected error occurred: {str(e)}")


# --- Lambda Handler ---


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event: dict, context: LambdaContext):
    """
    The main Lambda function handler.
    Delegates event processing to the APIGatewayRestResolver.
    """
    return app.resolve(event, context)


# --- Simple Unit Tests ---


class TestApiEndpoints(unittest.TestCase):
    mock_context = MagicMock(spec=LambdaContext)

    def test_list_products(self):
        event = {
            "httpMethod": "GET",
            "path": "/products",
            "requestContext": {"elb": {"targetGroupArn": "xxx"}},
            "headers": {},
            "body": None,
        }
        response = app.resolve(event, self.mock_context)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("products", body)

    def test_get_product(self):
        event = {
            "httpMethod": "GET",
            "path": "/products/prod1",
            "pathParameters": {"product_id": "prod1"},
            "requestContext": {"elb": {"targetGroupArn": "xxx"}},
            "headers": {},
            "body": None,
        }
        response = app.resolve(event, self.mock_context)
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["name"], "Laptop")


if __name__ == "__main__":
    unittest.main()
