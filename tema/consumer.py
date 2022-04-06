"""
This module represents the Consumer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
from time import sleep


class Consumer(Thread):
    """
    Class that represents a consumer.
    """

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):
        """
        Constructor.

        :type carts: List
        :param carts: a list of add and remove operations

        :type marketplace: Marketplace
        :param marketplace: a reference to the marketplace

        :type retry_wait_time: Time
        :param retry_wait_time: the number of seconds that a producer must wait
        until the Marketplace becomes available

        :type kwargs:
        :param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self)
        self.carts = carts
        self.marketplace = marketplace
        self.retry_wait_time = retry_wait_time
        self.name = kwargs["name"]

    def run(self):
        """
        This function describes what a consumer is doing.
        """
        # For each cart
        for cart in self.carts:
            # Register cart
            cart_id = self.marketplace.new_cart()
            # For each operation in the cart
            for operation in cart:
                # If the operation is an add
                if operation["type"] == "add":
                    for _ in range(operation["quantity"]):
                        while not self.marketplace.add_to_cart(cart_id, operation["product"]):
                            # Wait if product is unavailable
                            sleep(self.retry_wait_time)
                elif operation["type"] == "remove":
                    # If the operation is a remove
                    for _ in range(operation["quantity"]):
                        self.marketplace.remove_from_cart(cart_id, operation["product"])
            # After all operations, place the order
            order = self.marketplace.place_order(cart_id)
            # Print the result of placing the order
            for product in order:
                print("{0} bought {1}".format(self.name, product))
