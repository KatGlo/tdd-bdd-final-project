# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods


class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""
    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        for _ in range(5):
            product = ProductFactory()
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_name_not_found(self):
        """It should return empty when name not found"""
        found = Product.find_by_name("NonExistentProduct")
        self.assertEqual(found.count(), 0)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_deserialize_bad_data(self):
        """It should not Deserialize a product with bad data"""
        product = Product()
        bad_data = "not a dictionary"
        with self.assertRaises(DataValidationError):
            product.deserialize(bad_data)

    def test_deserialize_missing_name(self):
        """It should not Deserialize a product with missing name"""
        product = Product()
        data = {"price": 10.0, "available": True, "category": "Books"}
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_find_product_not_found(self):
        """It should return None when searching for a nonexistent Product"""
        self.assertIsNone(Product.find(9999))

    def test_deserialize_valid(self):
        """It should correctly deserialize a valid Product dictionary"""
        product = Product()
        data = {
            "name": "Book",
            "description": "A sci-fi novel",
            "price": "19.99",
            "available": True,
            "category": "FOOD"
        }
        product.deserialize(data)
        self.assertEqual(product.name, data["name"])
        self.assertEqual(product.description, data["description"])
        self.assertEqual(product.price, Decimal(data["price"]))
        self.assertEqual(product.available, data["available"])
        self.assertEqual(product.category, Category.FOOD)

    def test_deserialize_invalid_category(self):
        """It should raise an error for an invalid category value"""
        product = Product()
        data = {
            "name": "Book",
            "description": "Sci-fi",
            "price": 29.99,
            "available": True,
            "category": "INVALID"
        }
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_deserialize_missing_fields(self):
        """It should raise an error when required fields are missing"""
        base_data = {
            "name": "Book",
            "description": "A book",
            "price": 10.0,
            "available": True,
            "category": "FOOD"
        }
        for key in ["description", "price", "available", "category"]:
            data = base_data.copy()
            del data[key]
            product = Product()
            with self.assertRaises(DataValidationError):
                product.deserialize(data)

    def test_deserialize_invalid_type(self):
        """It should raise an error when data is not a dictionary"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize("not a dict")

    def test_deserialize_invalid_boolean(self):
        """It should raise an error when 'available' is not a boolean"""
        product = Product()
        data = {
            "name": "Book",
            "description": "Invalid bool",
            "price": 10.0,
            "available": "yes",
            "category": "FOOD"
        }
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

    def test_find_by_category_not_found(self):
        """It should return empty when category not found"""
        self.assertEqual(Product.find_by_category(Category.TOOLS).count(), 0)

    def test_deserialize_empty_dict(self):
        """It should raise error when deserializing from empty dict"""
        product = Product()
        with self.assertRaises(DataValidationError):
            product.deserialize({})

    def test_find_by_name_empty(self):
        """It should handle find_by_name on empty DB"""
        result = Product.find_by_name("Anything")
        self.assertEqual(result.count(), 0)

    def test_find_by_category_empty(self):
        """It should handle find_by_category on empty DB"""
        result = Product.find_by_category(Category.FOOD)
        self.assertEqual(result.count(), 0)

    def test_deserialize_attribute_error(self):
        """It should raise DataValidationError on invalid attribute in category"""
        product = Product()
        data = {
            "name": "Book",
            "description": "Test",
            "price": 10.0,
            "available": True,
            "category": None
        }
        with self.assertRaises(DataValidationError):
            product.deserialize(data)

