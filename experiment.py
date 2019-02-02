"""Bartlett's transmission chain experiment from Remembering (1932)."""

import logging

from dallinger.config import get_config

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dallinger.experiment import Experiment


logger = logging.getLogger(__file__)


class Spaceship(Experiment):
    """Define the structure of the experiment."""

    def __init__(self, session=None):
        """Call the same function in the super (see experiments.py in dallinger).

        The models module is imported here because it must be imported at
        runtime.

        A few properties are then overwritten.

        Finally, setup() is called.
        """
        super(Spaceship, self).__init__(session)

        self.practice_repeats = 4
        self.experiment_repeats = 4
        self.generations = 10
        self.generation_size = 20

        import models
        self.models = models
        self.initial_recruitment_size = 1
        if session:
            self.setup()

    def setup(self):
        """Setup the networks.

        Setup only does stuff if there are no networks, this is so it only
        runs once at the start of the experiment. It first calls the same
        function in the super (see experiments.py in dallinger). Then it adds a
        source to each network.
        """
        if not self.networks():
            super(Spaceship, self).setup()
            for i,net in enumerate(self.networks()):
                self.models.ShipSource(network=net, image_set=i)

    def create_network(self):
        """Return a new network."""
        return self.models.ParticleNetwork(generations = self.generations, generation_size = self.generation_size)

    def create_node(self, network, participant):
        """Make a new node for participants."""
        return self.models.Particle(network=network,participant=participant)

    def add_node_to_network(self, node, network):
        """Add node to the chain and receive transmissions."""
        network.add_node(node)
        parents = node.neighbors(direction="from")
        if len(parents):
            parent = parents[0]
            parent.transmit()
        node.receive()

    @property
    def recruiter(self):

        from dallinger.recruiters import HotAirRecruiter

        config = get_config()
        try:
            debug_mode = config.get('mode', None) == 'debug'
        except RuntimeError:
            # Config not yet loaded
            debug_mode = False

        if debug_mode:
            return HotAirRecruiter

        return self.models.MTurkRobustRecruiter.from_current_config

    def recruit(self):
        """Recruit one participant at a time until all networks are full."""
        if self.networks(full=False):
            self.recruiter().recruit(n=1)
        else:
            self.recruiter().close_recruitment()
