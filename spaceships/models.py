from dallinger.nodes import Source
from dallinger.nodes import Agent
from dallinger.models import Info
from dallinger.models import Network
from dallinger.recruiters import MTurkRecruiter

from sqlalchemy import Integer, String, Float
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import cast

import random
import json

class ShipSource(Source):

    __mapper_args__ = {
        "polymorphic_identity": "ship_source"
    }

    def __init__(self, network, image_set, participant=None):
        super(Source, self).__init__(network, participant)
        self.image_set = image_set

    @hybrid_property
    def source_contents(self):
        """Convert property2 to source_contents."""
        return self.property2

    @source_contents.setter
    def source_contents(self, contents):
        """Make generation settable."""
        self.property2 = contents

    @source_contents.expression
    def source_contents(self):
        """Make generation queryable."""
        return self.property2

    @hybrid_property
    def image_set(self):
        """Convert property3 to image_set."""
        return int(self.property3)

    @image_set.setter
    def image_set(self, image_set):
        """Make image_set settable."""
        self.property3 = image_set

    @image_set.expression
    def image_set(self):
        """Make generation queryable."""
        return cast(self.property3, Integer)

    def _contents(self):
        """Define the contents of new Infos.

        transmit() -> _what() -> create_information() -> _contents().
        """

        if self.source_contents is None:

            contents = {}

            n_turns = 20
            n_parts = 8
            n_evidence = 4

            good_prior = 0.5
            good_prob = 0.6
            bad_prob = 0.4

            part_probs = []
            for i in range(n_parts):
                if random.random() < good_prior:
                    part_probs += [good_prob]
                else:
                    part_probs += [bad_prob]

            fails = []
            for t in range(n_turns):
                fails += [[]]
                for i in range(n_parts):
                    fails[t] += [[]]
                    for j in range(n_evidence):
                        if random.random() < part_probs[i]:
                            fails[t][i] += ['success']
                        else:
                            fails[t][i] += ['fail']

            contents['set'] = self.image_set
            contents['turn'] = 0
            contents['part_probs'] = part_probs
            contents['fails'] = fails
            contents['action'] = ''

            contents = json.dumps(contents)

            self.source_contents = contents

        else:

            contents = self.source_contents

        return contents

class ParticleNetwork(Network):
    """A discrete generational network.

    A discrete generational network arranges agents into none-overlapping
    generations.

    generation_size dictates how many agents are in each generation,
    generations sets how many generations the network involves.

    Note that this network type assumes that agents have a property called
    generation. If you agents do not have this property it will not work.
    """

    __mapper_args__ = {"polymorphic_identity": "particle_network"}

    def __init__(self, generations, generation_size):
        """Endow the network with some persistent properties."""
        self.property1 = repr(generations)
        self.property2 = repr(generation_size)
        self.max_size = repr(generations * generation_size + 1)

    @property
    def generations(self):
        """The length of the network: the number of generations."""
        return int(self.property1)

    @property
    def generation_size(self):
        """The width of the network: the size of a single generation."""
        return int(self.property2)

    def add_node(self, node):
        """Link to the agent from a random parent"""

        nodes = [n for n in self.nodes() if not isinstance(n, Source) and n.id != node.id]

        if len(nodes) == 0:
            latest_gen = 0
            num_agents_in_latest = 0
        else:
            latest_gen = max([n.generation for n in nodes])
            num_agents_in_latest = sum([n.generation == latest_gen for n in nodes])

        if num_agents_in_latest == self.generation_size:
            curr_generation = latest_gen + 1
        else:
            curr_generation = latest_gen

        node.generation = curr_generation

        if curr_generation == 0:
            parent = self._select_oldest_source()
        else:
            parent = self._select_valid_node_from_generation(
                node_type=type(node),
                generation=curr_generation - 1)

        if parent is not None:

            parent.connect(whom=node)
            parent.transmit(to_whom=node)

            # if isinstance(parent, ShipSource):
            #     parent.transmit(to_whom=node)
            # else:
            #     parent.transmit(to_whom=node, what = Action)

    def _select_oldest_source(self):
        return self.nodes(type=Source)[0]

    def _select_valid_node_from_generation(self, node_type, generation):

        prev_agents = node_type.query\
            .filter_by(failed=False,
                       network_id=self.id,
                       generation=(generation))\
            .all()

        return random.choice(prev_agents)

class Particle(Agent):

    __mapper_args__ = {"polymorphic_identity": "particle"}

    def __init__(self, network, participant=None):
        super(Agent, self).__init__(network, participant)

    @hybrid_property
    def generation(self):
        """Convert property2 to genertion."""
        return int(self.property2)

    @generation.setter
    def generation(self, generation):
        """Make generation settable."""
        self.property2 = repr(generation)

    @generation.expression
    def generation(self):
        """Make generation queryable."""
        return cast(self.property2, Integer)

class MTurkRobustRecruiter(MTurkRecruiter):

    def recruit(self, n=1):

        hit_request = {
            'max_assignments': n,
            'title': self.config.get('title'),
            'description': self.config.get('description'),
            'keywords': self._config_to_list('keywords'),
            'reward': self.config.get('base_payment'),
            'duration_hours': self.config.get('duration'),
            'lifetime_days': self.config.get('lifetime'),
            'ad_url': self.ad_url,
            'notification_url': self.config.get('notification_url'),
            'approve_requirement': self.config.get('approve_requirement'),
            'us_only': self.config.get('us_only'),
            'blacklist': self._config_to_list('qualification_blacklist'),
        }
        hit_info = self.mturkservice.create_hit(**hit_request)
        if self.config.get('mode') == "sandbox":
            lookup_url = "https://workersandbox.mturk.com/mturk/preview?groupId={type_id}"
        else:
            lookup_url = "https://worker.mturk.com/mturk/preview?groupId={type_id}"

        return
