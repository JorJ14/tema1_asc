"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
from threading import Lock


class QueueElement:
    """
    Class that represents a Product inside a Queue.
    Contains a Product and an available flag.
    """
    def __init__(self, product):
        self.product = product
        self.available = True

    def set_unavailable(self):
        self.available = False

    def set_available(self):
        self.available = True


class CartElement:
    """
    Class that represents a Product inside a Cart.
    Contains a Product and the producer_id.
    """
    def __init__(self, product, producer_id):
        self.product = product
        self.producer_id = producer_id


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
        #self.lock = Lock()

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        self.producer_id_lock.acquire()
        producer_id_string = "prod{0}".format(self.producer_id)
        self.producers[producer_id_string] = []
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
        producer_list = self.producers[producer_id]
        if producer_list is None:
            return False
        if len(producer_list) == self.queue_size_per_producer:
            return False
        #self.lock.acquire()
        self.producers[producer_id].append(QueueElement(product))
        #self.lock.release()
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

        #self.lock.acquire()
        for producer_id in range(max_producer_id):
            producer_id_string = "prod{0}".format(producer_id)
            producer_list = self.producers[producer_id_string]
            for i in range(len(producer_list)):
                element = producer_list[i]
                if element.product == product and element.available:
                    self.carts[cart_id].append(CartElement(product, producer_id_string))
                    self.producers[producer_id_string][i].set_unavailable()
                    #self.lock.release()
                    return True
        #self.lock.release()
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
        #self.lock.acquire()
        for cart_element in cart_list:
            if cart_element.product == product:
                producer_id = cart_element.producer_id
                producer_list = self.producers[producer_id]
                for i in range(len(producer_list)):
                    element = producer_list[i]
                    if element.product == product and not element.available:
                        self.carts[cart_id].remove(cart_element)
                        self.producers[producer_id][i].set_available()
                        #self.lock.release()
                        return True
        #self.lock.release()
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

        #self.lock.acquire()
        for cart_element in cart_list:
            product = cart_element.product
            result.append(product)
            producer_id = cart_element.producer_id
            producer_list = self.producers[producer_id]
            for element in producer_list:
                if element.product == product and not element.available:
                    self.producers[producer_id].remove(element)
                    break
        #self.lock.release()
        return result
