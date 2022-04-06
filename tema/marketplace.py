"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
from threading import Lock


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

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
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
        # Acquire the lock which protects the queue size of the producer
        self.producers_locks[producer_id].acquire()
        # Extracts the queue size
        queue_size = self.producers_queue[producer_id]
        # If queue is full, we cannot publish the product
        if queue_size == self.queue_size_per_producer:
            # Release the lock
            self.producers_locks[producer_id].release()
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
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        # Acquire the lock which protects cart_id
        self.cart_id_lock.acquire()
        cart_id = self.cart_id
        # Creates new cart with cart_id
        self.carts[cart_id] = []
        # Increments cart_id
        self.cart_id += 1
        # Release the lock
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
        # Checks if cart with cart_id exists
        if cart_id not in self.carts:
            return False
        # Checks if product is available at any producer
        if product.name not in self.products_producers:
            return False
        self.products_locks[product.name].acquire()
        if not self.products_producers[product.name]:
            self.products_locks[product.name].release()
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
        return True

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        # Checks if cart_id exists
        if cart_id not in self.carts:
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
                return True
        return False

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        result = []
        # Checks if cart with cart_id exists
        if cart_id not in self.carts:
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
        return result
