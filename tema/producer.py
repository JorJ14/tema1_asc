"""
This module represents the Producer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
from time import sleep


class Producer(Thread):
    """
    Class that represents a producer.
    """

    def __init__(self, products, marketplace, republish_wait_time, **kwargs):
        """
        Constructor.

        @type products: List()
        @param products: a list of products that the producer will produce

        @type marketplace: Marketplace
        @param marketplace: a reference to the marketplace

        @type republish_wait_time: Time
        @param republish_wait_time: the number of seconds that a producer must
        wait until the marketplace becomes available

        @type kwargs:
        @param kwargs: other arguments that are passed to the Thread's __init__()
        """
        # Set daemon = True, to create a background thread
        Thread.__init__(self, daemon=True)
        self.products = products
        self.marketplace = marketplace
        self.republish_wait_time = republish_wait_time
        self.name = kwargs["name"]

    def run(self):
        """
        This function describes what a producer is doing.
        """
        # Register the producer
        producer_id = self.marketplace.register_producer()
        # Publish products
        while True:
            # Publish each product
            for element in self.products:
                # Extract product, quantity and production time
                product = element[0]
                quantity = element[1]
                production_time = element[2]
                # Wait to finish production
                sleep(production_time)
                # Publish the product
                for _ in range(quantity):
                    while not self.marketplace.publish(producer_id, product):
                        # Wait if queue is full
                        sleep(self.republish_wait_time)
