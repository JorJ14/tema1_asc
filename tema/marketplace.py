"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
from threading import Lock
import unittest


class QueueElement:
    """
    Class that represents a Product inside a Queue.
    Contains a Product and an available flag.
    """

    def __init__(self, product):
        self.product = product
        self.cart = -1
        self.available = True

    def set_unavailable(self):
        """
        Sets element unavailable for consumers.
        """
        self.available = False

    def set_available(self):
        """
        Sets element available for consumers.
        """
        self.available = True

    def set_cart(self, cart_id):
        """
        Reserves the product for a cart
        """
        self.cart = cart_id


class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """

    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """
        self.queue_size_per_producer = queue_size_per_producer
        self.producers = {}
        self.carts = {}
        self.producer_id = 0
        self.cart_id = 0
        self.producer_id_lock = Lock()
        self.cart_id_lock = Lock()
        self.producers_locks = {}

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        self.producer_id_lock.acquire()
        producer_id_string = "prod{0}".format(self.producer_id)
        self.producers[producer_id_string] = []
        self.producers_locks[producer_id_string] = Lock()
        self.producer_id += 1
        self.producer_id_lock.release()
        return producer_id_string

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """
        self.producers_locks[producer_id].acquire()
        producer_list = self.producers[producer_id]
        if producer_list is None:
            self.producers_locks[producer_id].release()
            return False
        if len(producer_list) == self.queue_size_per_producer:
            self.producers_locks[producer_id].release()
            return False
        self.producers[producer_id].append(QueueElement(product))
        self.producers_locks[producer_id].release()
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        self.cart_id_lock.acquire()
        cart_id = self.cart_id
        self.carts[cart_id] = []
        self.cart_id += 1
        self.cart_id_lock.release()
        return cart_id

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """
        cart_list = self.carts[cart_id]
        if cart_list is None:
            return False
        self.producer_id_lock.acquire()
        max_producer_id = self.producer_id
        self.producer_id_lock.release()

        for producer_id in range(max_producer_id):
            producer_id_string = "prod{0}".format(producer_id)
            self.producers_locks[producer_id_string].acquire()
            producer_list = self.producers[producer_id_string]
            for element in producer_list:
                if element.product == product and element.available:
                    self.carts[cart_id].append({"product": product,
                                                "producer_id": producer_id_string})
                    element.set_unavailable()
                    element.set_cart(cart_id)
                    self.producers_locks[producer_id_string].release()
                    return True
            self.producers_locks[producer_id_string].release()
        return False

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        cart_list = self.carts[cart_id]
        if cart_list is None:
            return False
        for cart_element in cart_list:
            if cart_element["product"] == product:
                producer_id = cart_element["producer_id"]
                self.producers_locks[producer_id].acquire()
                producer_list = self.producers[producer_id]
                for element in producer_list:
                    if (element.product == product and element.cart == cart_id
                            and not element.available):
                        self.carts[cart_id].remove(cart_element)
                        element.set_available()
                        self.producers_locks[producer_id].release()
                        return True
                self.producers_locks[producer_id].release()
        return False

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        result = []
        cart_list = self.carts[cart_id]
        if cart_list is None:
            return None

        for cart_element in cart_list:
            product = cart_element["product"]
            result.append(product)
            producer_id = cart_element["producer_id"]
            self.producers_locks[producer_id].acquire()
            producer_list = self.producers[producer_id]
            for element in producer_list:
                if (element.product == product and element.cart == cart_id
                        and not element.available):
                    self.producers[producer_id].remove(element)
                    break
            self.producers_locks[producer_id].release()
        self.carts[cart_id] = []
        return result


class TestMarketplace(unittest.TestCase):
    """
    Unit testing class for Marketplace functionalities.
    """

    def setUp(self):
        """
        Set up method for tests.
        Instantiate Marketplace with max_queue_size = 5
        """
        self.marketplace = Marketplace(5)
        self.product0 = {
            "product_type": "Coffee",
            "name": "Indonezia",
            "acidity": 5.05,
            "roast_level": "MEDIUM",
            "price": 1
        }
        self.product1 = {
            "product_type": "Tea",
            "name": "Linden",
            "type": "Herbal",
            "price": 9
        }
        self.product2 = {
            "product_type": "Coffee",
            "name": "Ethiopia",
            "acidity": 5.09,
            "roast_level": "MEDIUM",
            "price": 10
        }
        self.product3 = {
            "product_type": "Coffee",
            "name": "Arabica",
            "acidity": 5.02,
            "roast_level": "MEDIUM",
            "price": 9
        }

    def test_register_producer(self):
        """
        Tests that producer_id is generated as expected.
        """
        self.assertEqual(self.marketplace.register_producer(), 'prod0',
                         'Incorrect producer_id assigned for first producer!')
        self.assertEqual(self.marketplace.register_producer(), 'prod1',
                         'Incorrect producer_id assigned for second producer!')
        self.assertEqual(self.marketplace.register_producer(), 'prod2',
                         'Incorrect producer_id assigned for third producer!')

    def test_publish(self):
        """
        Tests that a producer can publish products.
        Tests that a producer cannot publish products when his queue is full.
        """
        self.test_register_producer()

        for _ in range(3):
            check = self.marketplace.publish('prod0', self.product0)
            self.assertTrue(check, 'Producer prod0 should be able to publish product!')
        for _ in range(2):
            check = self.marketplace.publish('prod0', self.product1)
            self.assertTrue(check, 'Producer prod0 should be able to publish product!')
        check = self.marketplace.publish('prod0', self.product0)
        self.assertFalse(check, 'Producer prod0 should not be able to publish product!')

        index = 0
        for element in self.marketplace.producers['prod0']:
            if index < 3:
                self.assertTrue(element.product == self.product0 and element.available,
                                'Producer prod0 published wrong product!')
            else:
                self.assertTrue(element.product == self.product1 and element.available,
                                'Producer prod0 published wrong product!')
            index += 1

        for _ in range(2):
            check = self.marketplace.publish('prod1', self.product2)
            self.assertTrue(check, 'Producer prod1 should be able to publish product!')
        check = self.marketplace.publish('prod1', self.product3)
        self.assertTrue(check, 'Producer prod1 should be able to publish product!')
        check = self.marketplace.publish('prod1', self.product1)
        self.assertTrue(check, 'Producer prod1 should be able to publish product!')
        index = 0
        for element in self.marketplace.producers['prod1']:
            if index < 2:
                self.assertTrue(element.product == self.product2 and element.available,
                                'Producer prod1 published wrong product!')
            elif index == 2:
                self.assertTrue(element.product == self.product3 and element.available,
                                'Producer prod1 published wrong product!')
            else:
                self.assertTrue(element.product == self.product1 and element.available,
                                'Producer prod1 published wrong product!')
            index += 1

    def test_new_cart(self):
        """
        Tests new_cart method.
        """
        self.test_publish()
        self.assertEqual(self.marketplace.new_cart(), 0,
                         'Incorrect cart_id assigned for first cart!')
        self.assertEqual(self.marketplace.new_cart(), 1,
                         'Incorrect cart_id assigned for second cart!')
        self.assertEqual(self.marketplace.new_cart(), 2,
                         'Incorrect cart_id assigned for third cart!')
        self.assertEqual(self.marketplace.new_cart(), 3,
                         'Incorrect cart_id assigned for fourth cart!')
        for i in range(4):
            self.assertEqual(self.marketplace.carts[i], [],
                             'Cart should be empty!')

    def test_add_to_cart(self):
        """
        Test add_to_cart method.
        """
        self.test_new_cart()
        for _ in range(3):
            self.assertTrue(self.marketplace.add_to_cart(0, self.product1),
                            'Cannot add product1 to cart!')
        self.assertFalse(self.marketplace.add_to_cart(0, self.product1),
                         'Should not be able to add product1 to cart!')
        self.assertEqual(len(self.marketplace.carts[0]), 3,
                         'Wrong number of products added to cart!')
        self.assertTrue(self.marketplace.add_to_cart(0, self.product2),
                        'Cannot add product2 to cart!')
        self.assertTrue(self.marketplace.add_to_cart(1, self.product2),
                        'Cannot add product2 to cart!')
        self.assertFalse(self.marketplace.add_to_cart(1, self.product2),
                         'Should not be able to add product2 to cart!')
        self.assertEqual(len(self.marketplace.carts[1]), 1,
                         'Wrong number of products added to cart!')
        # Checks if products are available/unavailable
        for element in self.marketplace.producers['prod0']:
            if element.product == self.product1:
                self.assertFalse(element.available,
                                 'Product should be unavailable!')
                self.assertEqual(element.cart, 0,
                                 'Product should be reserved in cart0!')
            elif element.product == self.product0:
                self.assertTrue(element.available,
                                'Product should be available!')

    def test_remove_from_cart(self):
        """
        Tests remove_from_cart method.
        """
        self.test_add_to_cart()
        self.assertTrue(self.marketplace.remove_from_cart(0, self.product1),
                        'Cannot remove product1 from cart!')
        self.assertEqual(len(self.marketplace.carts[0]), 3,
                         'Wrong number of products in cart0!')
        self.assertFalse(self.marketplace.remove_from_cart(0, self.product3),
                         'Should not be able to remove this product!')
        unavailable_product1 = 0
        for element in self.marketplace.producers['prod0']:
            if element.product == self.product1 and not element.available:
                unavailable_product1 += 1
        self.assertEqual(unavailable_product1, 1,
                         'Wrong number of unavailable product1 in prod0 queue')

    def test_place_order(self):
        """
        Tests place_order method.
        """
        self.test_remove_from_cart()
        self.assertEqual(self.marketplace.place_order(0),
                         [self.product1, self.product1, self.product2],
                         'Wrong cart list!')
        # Checks if products are removed from producer's queue
        self.assertEqual(len(self.marketplace.producers['prod0']), 4,
                         'Wrong number of products in prod0 queue!')
        self.assertEqual(len(self.marketplace.producers['prod1']), 2,
                         'Wrong number of products in prod1 queue!')
        # Checks if products are removed from cart
        self.assertEqual(self.marketplace.carts[0], [],
                         'Cart0 should be empty!')
