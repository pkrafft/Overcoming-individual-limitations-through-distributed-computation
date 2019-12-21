"""Bartlett's transmission chain experiment from Remembering (1932)."""

import logging
# import pysnooper

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import Integer, and_, func
import random
import json

from sqlalchemy import and_, func
from sqlalchemy.sql.expression import cast
from dallinger.bots import BotBase
from dallinger.config import get_config
from dallinger.networks import Chain
from dallinger.experiment import Experiment


logger = logging.getLogger(__file__)


def extra_parameters():
    config = get_config()
    config.register("num_participants", int)

DEBUG = True


class Bartlett1932(Experiment):
    """Define the structure of the experiment."""

    def __init__(self, session=None):
        """Call the same function in the super (see experiments.py in dallinger).

        A few properties are then overwritten.

        Finally, setup() is called.
        """
        super(Bartlett1932, self).__init__(session)
        from . import models  # Import at runtime to avoid SQLAlchemy warnings

        self.models = models
        self.bonus_amount = 0.5
        self.experiment_repeats = 1
        self.initial_recruitment_size = self.generation_size = 1
        self.generations = 3
        self.num_practice_networks_per_experiment = 1 if DEBUG else 4
        self.num_fixed_order_experimental_networks_per_experiment = 0
        self.num_random_order_experimental_networks_per_experiment = 0 if DEBUG else 4
        self.num_experimental_networks_per_experiment = self.num_fixed_order_experimental_networks_per_experiment + self.num_random_order_experimental_networks_per_experiment
        self.num_networks_per_experiment_total = self.num_practice_networks_per_experiment + self.num_random_order_experimental_networks_per_experiment + self.num_fixed_order_experimental_networks_per_experiment
        self.nodes_per_generation = self.generation_size * self.num_networks_per_experiment_total
        if session:
            self.setup()

    def configure(self):
        config = get_config()
        self.num_participants = config.get("num_participants")

    def setup(self):
        """Setup the networks"""

        """Create the networks if they don't already exist."""
        if not self.networks():
            for p in range(self.num_practice_networks_per_experiment):
                network = self.create_network(role = 'practice', decision_index = p)
                self.models.WarOfTheGhostsSource(network=network)

            for f in range(self.num_fixed_order_experimental_networks_per_experiment):
                decision_index = self.num_practice_networks_per_experiment + f
                network = self.create_network(role = 'experiment', decision_index = decision_index)
                self.models.WarOfTheGhostsSource(network=network)

            for r in range(self.num_random_order_experimental_networks_per_experiment):
                decision_index = self.num_practice_networks_per_experiment + self.num_fixed_order_experimental_networks_per_experiment + r
                network = self.create_network(role = 'experiment', decision_index = decision_index)
                self.models.WarOfTheGhostsSource(network=network)
            self.session.commit()

    def create_node(self, network, participant):
        return self.models.Particle(network=network,participant=participant)

    def create_network(self, role, decision_index):
        """Return a new network."""
        net = self.models.ParticleFilter(generations = self.generations, generation_size = self.generation_size)
        net.role = role
        net.decision_index = decision_index
        self.session.add(net)
        return net

    def add_node_to_network(self, node, network):
        """Add node to the chain and receive transmissions."""
        network.add_node(node)
        parents = node.neighbors(direction="from")
        # if len(parents):
        #     parent = parents[0]
        #     parent.transmit()
        node.receive()

    # @pysnooper.snoop()
    def get_network_for_existing_participant(self, participant, participant_nodes):
        """Obtain a netwokr for a participant who has already been assigned to a condition by completeing earlier rounds"""

        # which networks has this participant already completed?
        networks_participated_in = [node.network_id for node in participant_nodes]

        # How many decisions has the particiapnt already made?
        completed_decisions = len(networks_participated_in)

        # When the participant has completed all networks in their condition, their experiment is over
        # returning None throws an error to the fronted which directs to questionnaire and completion
        if completed_decisions == self.num_practice_networks_per_experiment + self.num_experimental_networks_per_experiment:
            return None

        nfixed = self.num_practice_networks_per_experiment + self.num_fixed_order_experimental_networks_per_experiment

        # If the participant must still follow the fixed network order
        if completed_decisions < nfixed:
            # find the network that is next in the participant's schedule
            # match on completed decsions b/c decision_index counts from zero but completed_decisions count from one
            return self.models.Network.query.filter(self.models.Network.property4 == repr(completed_decisions)).filter_by(full = False).one()

        # If it is time to sample a network at random
        else:
            # find networks which match the participant's condition and werent' fixed order nets
            matched_condition_experimental_networks = self.models.Network.query.filter(cast(self.models.Network.property4, Integer) >= nfixed).filter_by(full = False).all()

            # subset further to networks not already participated in (because here decision index doesnt guide use)
            availible_options = [net for net in matched_condition_experimental_networks if net.id not in networks_participated_in]

            # choose randomly among this set
            chosen_network = random.choice(availible_options)

        return chosen_network

    # #@pysnooper.snoop(prefix = "@snoop: ")
    def get_network_for_new_participant(self, participant):
        key = "experiment.py >> get_network_for_new_participant ({}); ".format(participant.id)

        # Return first-trial networks
        return self.models.ParticleFilter.query.filter_by(full = False).filter(self.models.ParticleFilter.property4 == repr(0)).one_or_none()

    #@pysnooper.snoop()
    def get_network_for_participant(self, participant):
        """Find a network for a participant."""
        key = "experiment.py >> get_network_for_participant ({}); ".format(participant.id)
        participant_nodes = participant.nodes()
        if not participant_nodes:
            chosen_network = self.get_network_for_new_participant(participant)
        else:
            chosen_network = self.get_network_for_existing_participant(participant, participant_nodes)

        if chosen_network is not None:
            self.log("Assigned to network: {}; Decsion Index: {};".format(chosen_network.id, chosen_network.decision_index), key)

        else:
            self.log("Requested a network but was assigned None.".format(len(participant_nodes)), key)

        return chosen_network

    # @pysnooper.snoop()
    def get_current_generation(self):
        network = self.models.ParticleFilter.query.first()
        return repr(int(network.property3))

    def rollover_generation(self):
        for network in self.models.ParticleFilter.query.all():
            network.current_generation = int(network.current_generation) + 1
        self.session.commit()
        self.log("Rolled over all network to generation {}".format(network.current_generation), "experiment.py >> rollover_generation: ")

    # @pysnooper.snoop()
    def recruit(self):
        key = "experiment.py >> recruit: "
        """Recruit one participant at a time until all networks are full."""
        if self.networks(full=False):
            current_generation = self.get_current_generation()

            completed_participant_ids = [p.id for p in self.models.Participant.query.filter_by(failed = False, status = "approved")]

            # particle.property3 = generation
            completed_nodes_this_generation = self.models.Particle.query.filter(
                                                                            and_(self.models.Particle.property3 == current_generation, \
                                                                            self.models.Particle.participant_id.in_(completed_participant_ids))) \
                                                                        .count()
            self.log("G: {}; Approved ps: {} Required ps: {}".format(current_generation, int(float(completed_nodes_this_generation) / float(self.num_experimental_networks_per_experiment + self.num_practice_networks_per_experiment)), self.generation_size), key)

            if completed_nodes_this_generation == self.nodes_per_generation:
                self.log("Generation Complete. Rolling over and recruiting.", key)
                self.rollover_generation()
                self.recruiter.recruit(n=self.generation_size)

        else:
            self.recruiter.close_recruitment()

    def data_check(self, participant):
        infos = participant.infos()
        if len(infos) < self.num_practice_networks_per_experiment + self.num_experimental_networks_per_experiment:
            return False
        return True

    def bonus(self, participant):
        infos = participant.infos()
        if not infos:
            return 0
        successes = []
        for info in infos:
            data = json.loads(info.contents)

            # only count test trials
            if data["task"] >= self.num_practice_networks_per_experiment:
                if "choice" in data.keys() and "true_class" in data.keys():
                    n_classes = len(data["classes"])
                    true_pos = len(set(data["choice"]).intersection(data["true_class"]))
                    total_neg = n_classes - len(data["true_class"])
                    false_pos = len(set(data["choice"]) - set(data["true_class"]))
                    true_neg = total_neg - false_pos
                    successes.append((true_pos + true_neg)/8.0)
        if len(successes) == 0:
            return 0
        success_rate = float(sum(successes)) / float(len(successes))
        return min([self.bonus_amount, self.bonus_amount * success_rate])
