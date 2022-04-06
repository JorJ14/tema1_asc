"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
import time
from threading import Lock
import unittest
import logging
from logging.handlers import RotatingFileHandler
from tema.product import Coffee, Tea


class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """
        self.queue_size_per_producer = queue_size_per_producer
        # Dictionary with key: producer_id, value: number of products in queue
        self.producers_queue = {}
        # Dictionary with key: cart_id, value: list of products from cart
        self.carts = {}
        # Variable used to register producers
        self.producer_id = 0
        # Variable used to add new carts
        self.cart_id = 0
        # Lock used to avoid race condition from producers register
        self.producer_id_lock = Lock()
        # Lock used to avoid race condition from adding new carts
        self.cart_id_lock = Lock()
        # Dictionary with key: producer_id, value: a Lock used to avoid race condition when
        # we modify the queue size of the producer (for example the producer publish a product
        # and a consumer places an order which contains products from this producer)
        self.producers_locks = {}
        # Dictionary with key: product_name, value: the list of producer_ids who have
        # the products available
        self.products_producers = {}
        # Dictionary with key: product_name, value: a Lock used to avoid the situation:
        # product1 is available only from producer0 (quantity = 1) and two consumers
        # wants to add product1 to their carts. Both checks if the products is available and
        # after that each one pops the queue products_producers[product1.name] and the second
        # pop will give us an error (we will pop an empty queue)
        self.products_locks = {}
        # Used for logging
        self.logger = logging.getLogger('my_logger')
        self.logger.setLevel(logging.INFO)
        self.handler = RotatingFileHandler("marketplace.log", maxBytes=1024 * 512, backupCount=20)
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.handler.setFormatter(self.formatter)
        self.formatter.converter = time.gmtime
        self.logger.addHandler(self.handler)

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        self.logger.info("Entered register_producer()!")
        # Acquire the lock which protects producer_id
        self.producer_id_lock.acquire()
        # Builds the producer_id string
        producer_id_string = "prod{0}".format(self.producer_id)
        # Queue of this producer will be empty
        self.producers_queue[producer_id_string] = 0
        # Initialise the lock for this producer
        self.producers_locks[producer_id_string] = Lock()
        # Increments the id
        self.producer_id += 1
        # Release the lock which protects producer_id
        self.producer_id_lock.release()
        self.logger.info("Finished register_producer(): returned producer_id: %s!",
                         producer_id_string)
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
        self.logger.info("Entered publish(%s, %s)!", producer_id, product)
        # Acquire the lock which protects the queue size of the producer
        self.producers_locks[producer_id].acquire()
        # Extracts the queue size
        queue_size = self.producers_queue[producer_id]
        # If queue is full, we cannot publish the product
        if queue_size == self.queue_size_per_producer:
            # Release the lock
            self.producers_locks[producer_id].release()
            self.logger.info("Finished publish(%s, %s): Queue is Full!",
                             producer_id, product)
            return False
        # Marks the product as available at producer_id
        if product.name not in self.products_producers:
            self.products_locks[product.name] = Lock()
            self.products_locks[product.name].acquire()
            self.products_producers[product.name] = []
        else:
            self.products_locks[product.name].acquire()
        self.products_producers[product.name].append(producer_id)
        self.products_locks[product.name].release()
        # Increments queue size
        self.producers_queue[producer_id] += 1
        # Release the lock
        self.producers_locks[producer_id].release()
        self.logger.info("Finished publish(%s, %s): Published product!",
                         producer_id, product)
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        self.logger.info("Entered new_cart()!")
        # Acquire the lock which protects cart_id
        self.cart_id_lock.acquire()
        cart_id = self.cart_id
        # Creates new cart with cart_id
        self.carts[cart_id] = []
        # Increments cart_id
        self.cart_id += 1
        # Release the lock
        self.cart_id_lock.release()
        self.logger.info("Finished new_cart(): New cart: %d!", cart_id)
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
        self.logger.info("Entered add_to_cart(%d, %s)!", cart_id, product)
        # Checks if cart with cart_id exists
        if cart_id not in self.carts:
            self.logger.info("Finished add_to_cart(%d, %s): Cart doesn't exist!",
                             cart_id, product)
            return False
        # Checks if product is available at any producer
        if product.name not in self.products_producers:
            self.logger.info("Finished add_to_cart(%d, %s): Product is not available!",
                             cart_id, product)
            return False
        self.products_locks[product.name].acquire()
        if not self.products_producers[product.name]:
            self.products_locks[product.name].release()
            self.logger.info("Finished add_to_cart(%d, %s): Product is not available!",
                             cart_id, product)
            return False
        # Extracts one producer that has the product available
        # Makes product unavailable
        producer_id = self.products_producers[product.name].pop(0)
        self.products_locks[product.name].release()
        # Adds product to the cart, knowing what is the producer of the product
        # so in case of removing, the product will become available again from
        # this producer
        self.carts[cart_id].append({"product": product,
                                    "producer_id": producer_id})
        self.logger.info("Finished add_to_cart(%d, %s): Product added to cart!",
                         cart_id, product)
        return True

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        self.logger.info("Entered remove_from_cart(%d, %s)!", cart_id, product)
        # Checks if cart_id exists
        if cart_id not in self.carts:
            self.logger.info("Finished remove_from_cart(%d, %s): Cart doesn't exist!",
                             cart_id, product)
            return False
        # Extracts the cart list
        cart_list = self.carts[cart_id]
        # Search for the product in the list
        for cart_element in cart_list:
            if cart_element["product"] == product:
                # Makes product available from the producer
                producer_id = cart_element["producer_id"]
                self.products_producers[product.name].append(producer_id)
                # Removes product from cart
                self.carts[cart_id].remove(cart_element)
                self.logger.info("Finished remove_from_cart(%d, %s): Product removed from cart!",
                                 cart_id, product)
                return True
        self.logger.info("Finished remove_from_cart(%d, %s): Product not found in cart!",
                         cart_id, product)
        return False

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        self.logger.info("Entered place_order(%d)!", cart_id)
        result = []
        # Checks if cart with cart_id exists
        if cart_id not in self.carts:
            self.logger.info("Finished place_order(%d): Cart doesn't exist!", cart_id)
            return None
        # Extracts the cart list
        cart_list = self.carts[cart_id]
        # Remove each product from the queue of the producer who produced it
        for cart_element in cart_list:
            product = cart_element["product"]
            result.append(product)
            producer_id = cart_element["producer_id"]
            # Use the lock to avoid race condition
            self.producers_locks[producer_id].acquire()
            self.producers_queue[producer_id] -= 1
            self.producers_locks[producer_id].release()
        # Cleans the cart list
        self.carts[cart_id] = []
        self.logger.info("Finished place_order(%d): Order placed: %s!", cart_id, result)
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
        self.product0 = Coffee(name="Indonezia", acidity="5.05", roast_level="MEDIUM", price=1)
        self.product1 = Tea(name="Linden", type="Herbal", price=9)
        self.product2 = Coffee(name="Ethiopia", acidity="5.09", roast_level="MEDIUM", price=10)
        self.product3 = Coffee(name="Arabica", acidity="5.02", roast_level="MEDIUM", price=9)

    def test_register_producer(self):
        """
        Tests that producer_id is generated as expected.
        Registers 3 producers.
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
        # Prod0 publish 3 units of product0
        for _ in range(3):
            check = self.marketplace.publish('prod0', self.product0)
            self.assertTrue(check, 'Producer prod0 should be able to publish product!')
        # Prod0 publish 2 units of product1
        for _ in range(2):
            check = self.marketplace.publish('prod0', self.product1)
            self.assertTrue(check, 'Producer prod0 should be able to publish product!')
        # Now Prod0 queue is full. Should not be able to publish extra products
        check = self.marketplace.publish('prod0', self.product0)
        self.assertFalse(check, 'Producer prod0 should not be able to publish product!')
        # Prod1 publish 2 units of product 2
        for _ in range(2):
            check = self.marketplace.publish('prod1', self.product2)
            self.assertTrue(check, 'Producer prod1 should be able to publish product!')
        # Prod1 publish 1 unit of product3
        check = self.marketplace.publish('prod1', self.product3)
        self.assertTrue(check, 'Producer prod1 should be able to publish product!')
        # Prod1 publish 1 unit of product1
        check = self.marketplace.publish('prod1', self.product1)
        self.assertTrue(check, 'Producer prod1 should be able to publish product!')
        # Checks prod0 and prod1 queue sizes
        self.assertEqual(self.marketplace.producers_queue['prod0'], 5,
                         'Producer prod0 queue should be full!')
        self.assertEqual(self.marketplace.producers_queue['prod1'], 4,
                         'Producer prod1 queue size should be 4!')
        # Checks the available quantity for each product
        self.assertEqual(len(self.marketplace.products_producers[self.product0.name]), 3,
                         'Product0 should be available in quantity = 3!')
        self.assertEqual(len(self.marketplace.products_producers[self.product1.name]), 3,
                         'Product1 should be available in quantity = 3!')
        self.assertEqual(len(self.marketplace.products_producers[self.product2.name]), 2,
                         'Product2 should be available in quantity = 2!')
        self.assertEqual(len(self.marketplace.products_producers[self.product3.name]), 1,
                         'Product3 should be available in quantity = 1!')

    def test_new_cart(self):
        """
        Tests new_cart method.
        """
        self.test_publish()
        # Create 4 carts
        self.assertEqual(self.marketplace.new_cart(), 0,
                         'Incorrect cart_id assigned for first cart!')
        self.assertEqual(self.marketplace.new_cart(), 1,
                         'Incorrect cart_id assigned for second cart!')
        self.assertEqual(self.marketplace.new_cart(), 2,
                         'Incorrect cart_id assigned for third cart!')
        self.assertEqual(self.marketplace.new_cart(), 3,
                         'Incorrect cart_id assigned for fourth cart!')
        # Checks if carts lists are empty
        for i in range(4):
            self.assertEqual(self.marketplace.carts[i], [],
                             'Cart should be empty!')

    def test_add_to_cart(self):
        """
        Test add_to_cart method.
        """
        self.test_new_cart()
        # Add product0 to cart0
        self.assertTrue(self.marketplace.add_to_cart(0, self.product0),
                        'Cannot add product0 to cart!')
        # Add 3 units of product1 to cart0
        for _ in range(3):
            self.assertTrue(self.marketplace.add_to_cart(0, self.product1),
                            'Cannot add product1 to cart!')
        # Now, try to add one extra unit of product1 to cart0
        # There is no unit available, so it shouldn't be able to add to cart
        self.assertFalse(self.marketplace.add_to_cart(0, self.product1),
                         'Should not be able to add product1 to cart!')
        # Add 1 unit of product2 to cart0
        self.assertTrue(self.marketplace.add_to_cart(0, self.product2),
                        'Cannot add product2 to cart!')
        # Checks the size of cart0
        self.assertEqual(len(self.marketplace.carts[0]), 5,
                         'Wrong number of products added to cart!')
        # Add 1 unit of product2 to cart1
        self.assertTrue(self.marketplace.add_to_cart(1, self.product2),
                        'Cannot add product2 to cart!')
        # Now, try to add one extra unit of product2 to cart1
        # There is no unit available, so it shouldn't be able to add to cart
        self.assertFalse(self.marketplace.add_to_cart(1, self.product2),
                         'Should not be able to add product2 to cart!')
        # Checks the size of cart1
        self.assertEqual(len(self.marketplace.carts[1]), 1,
                         'Wrong number of products added to cart!')
        # Checks the available quantity for each product
        self.assertEqual(len(self.marketplace.products_producers[self.product0.name]), 2,
                         'Product0 should be available in quantity = 0!')
        self.assertEqual(len(self.marketplace.products_producers[self.product1.name]), 0,
                         'Product1 should be available in quantity = 3!')
        self.assertEqual(len(self.marketplace.products_producers[self.product2.name]), 0,
                         'Product2 should be available in quantity = 2!')
        self.assertEqual(len(self.marketplace.products_producers[self.product3.name]), 1,
                         'Product3 should be available in quantity = 1!')

    def test_remove_from_cart(self):
        """
        Tests remove_from_cart method.
        """
        self.test_add_to_cart()
        # Removes the first product1 from cart0
        self.assertTrue(self.marketplace.remove_from_cart(0, self.product1),
                        'Cannot remove product1 from cart!')
        # Checks if size of cart changed
        self.assertEqual(len(self.marketplace.carts[0]), 4,
                         'Wrong number of products in cart0!')
        # Now, try to remove product3 from cart0. Product3 is not in cart0,
        # so we should not be able to remove
        self.assertFalse(self.marketplace.remove_from_cart(0, self.product3),
                         'Should not be able to remove this product!')
        # Checks the available quantity for product1
        self.assertEqual(len(self.marketplace.products_producers[self.product1.name]), 1,
                         'Product1 should be available in quantity = 1!')

    def test_place_order(self):
        """
        Tests place_order method.
        """
        self.test_remove_from_cart()
        # Places order for cart0 and checks the result
        self.assertEqual(self.marketplace.place_order(0),
                         [self.product0, self.product1, self.product1, self.product2],
                         'Wrong cart list!')
        # Checks if products are removed from producer's queue
        self.assertEqual(self.marketplace.producers_queue['prod0'], 3,
                         'Producer prod0 queue contain 3 products!')
        self.assertEqual(self.marketplace.producers_queue['prod1'], 2,
                         'Producer prod1 queue should contain 2 products!')
        # Checks if products are removed from cart
        self.assertEqual(self.marketplace.carts[0], [],
                         'Cart0 should be empty!')
