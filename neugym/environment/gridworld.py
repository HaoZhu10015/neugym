import copy
import warnings

import networkx as nx
import numpy as np

import neugym as ng
from ._agent import _Agent
from ._object import _Object


__all__ = [
    "GridWorld"
]


class GridWorld:
    def __init__(self, origin_shape=(1, 1), origin_altitude_mat=None):
        if origin_altitude_mat is not None:
            if origin_altitude_mat.shape != origin_shape:
                msg = "Mismatch shape between origin {} and altitude matrix {}".format(origin_shape,
                                                                                       origin_altitude_mat.shape)
                raise ValueError(msg)
        else:
            origin_altitude_mat = np.zeros(origin_shape)

        self.world = nx.Graph()
        self.time = 0
        self.num_area = 0

        # Add origin.
        if origin_shape == (1, 1):
            self.world.add_node((0, 0, 0))
        else:
            m, n = origin_shape
            origin = nx.grid_2d_graph(m, n)
            mapping = {}
            for coord in origin.nodes:
                mapping[coord] = tuple([0] + list(coord))
            origin = nx.relabel_nodes(origin, mapping)
            self.world.update(origin)
        # Set origin altitude.
        self.set_altitude(0, origin_altitude_mat)

        self.alias = {}
        self.objects = []
        self.actions = ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))

        # Agent.
        self.agent = None

        # Reset state.
        self.has_reset_checkpoint = False
        self.reset_state = {
            "world": None,
            "time": None,
            "num_area": None,
            "alias": None,
            "objects": None,
            "agent": None
        }

    def add_area(self, shape, access_from=(0, 0, 0), access_to=(0, 0), register_action=None, altitude_mat=None):
        if not self.world.has_node(access_from):
            msg = "'access_from' coordinate {} out of world".format(access_from)
            raise ValueError(msg)

        if len(access_to) != 2:
            msg = "Tuple of length 2 expected for argument 'access_to', got {}".format(len(access_to))
            raise ValueError(msg)
        access_to = tuple([self.num_area + 1] + list(access_to))

        if altitude_mat is not None:
            if altitude_mat.shape != shape:
                msg = "Mismatch shape between area {} and altitude matrix {}".format(shape, altitude_mat.shape)
                raise ValueError(msg)
        else:
            altitude_mat = np.zeros(shape)

        world_backup = copy.deepcopy(self.world)

        m, n = shape
        new_area = nx.grid_2d_graph(m, n)
        mapping = {}
        for coord in new_area.nodes:
            mapping[coord] = tuple([self.num_area + 1] + list(coord))
        new_area = nx.relabel_nodes(new_area, mapping)

        self.world.update(new_area)
        self.num_area += 1

        try:
            self.add_path(access_from, access_to, register_action)
            self.set_altitude(self.num_area, altitude_mat)
        except Exception:
            self.world = world_backup
            self.num_area -= 1
            raise

    def remove_area(self, area_idx):
        new_world = copy.deepcopy(self.world)
        if area_idx == 0:
            raise ng.NeuGymPermissionError("Not allowed to remove origin area")

        # Remove area
        node_list = list(new_world.nodes)
        for node in node_list:
            if node[0] == area_idx:
                new_world.remove_node(node)
            elif node[0] > area_idx:
                new_label = tuple([node[0] - 1] + list(node[1:]))
                new_world = nx.relabel_nodes(new_world, {node: new_label})

        if not nx.is_connected(new_world):
            msg = "Not allowed to remove area {}, world would be no longer connected".format(area_idx)
            raise ng.NeuGymConnectivityError(msg)

        self.world = new_world
        self.num_area -= 1

        # Remove invalid alias.
        new_alias = {}
        for key, value in self.alias.items():
            if key[0] == area_idx:
                continue
            elif key[0] > area_idx:
                new_key = tuple([key[0] - 1] + list(key[1:]))
            else:
                new_key = key

            if value[0] == area_idx:
                continue
            elif value[0] > area_idx:
                new_value = tuple([value[0] - 1] + list(value[1:]))
            else:
                new_value = value
            new_alias[new_key] = new_value

        self.alias = new_alias

        # Remove objects in the area to be removed.
        new_objects = []
        for i, obj in enumerate(self.objects):
            if obj.coord[0] < area_idx:
                new_objects.append(obj)
            elif obj.coord[0] == area_idx:
                continue
            else:
                obj.coord = tuple([obj.coord[0] - 1] + list(obj.coord[1:]))
                new_objects.append(obj)
        self.objects = new_objects

    def add_path(self, coord_from, coord_to, register_action=None):
        if coord_from[0] == coord_to[0]:
            msg = "Not allowed to add path within an area"
            raise ng.NeuGymPermissionError(msg)

        if len(coord_from) != 3:
            msg = "Tuple of length 3 expected for argument 'coord_from', got {}".format(len(coord_from))
            raise ValueError(msg)
        if not self.world.has_node(coord_from):
            msg = "'coord_from' coordinate {} out of world".format(coord_from)
            raise ValueError(msg)
        if self.world.degree(coord_from) == 4:
            msg = "Maximum number of connections (4) for position {} reached, not allowed to access from it".format(
                coord_from)
            raise ng.NeuGymConnectivityError(msg)

        if len(coord_to) != 3:
            msg = "Tuple of length 3 expected for argument 'coord_to', got {}".format(len(coord_to))
            raise ValueError(msg)
        if not self.world.has_node(coord_to):
            msg = "'coord_to' coordinate {} out of world".format(coord_to)
            raise ValueError(msg)
        elif self.world.degree(coord_to) == 4:
            msg = "Maximum number of connections (4) for position {} reached, not allowed to access to it".format(
                coord_to)
            raise ng.NeuGymConnectivityError(msg)

        if (coord_from, coord_to) in self.world.edges:
            msg = "Path already exists between {} and {}".format(coord_from, coord_to)
            raise ng.NeuGymOverwriteError(msg)

        free_actions = []
        for action in self.actions:
            dx, dy = action
            alias_to = tuple([coord_from[0]] + [coord_from[1] + dx] + [coord_from[2] + dy])
            alias_from = tuple([coord_to[0]] + [coord_to[1] - dx] + [coord_to[2] - dy])
            if self.world.has_node(alias_to) or self.world.has_node(alias_from) or \
                    alias_to in self.alias.keys() or alias_from in self.alias.keys():
                continue
            free_actions.append(action)

        if len(free_actions) == 0:
            msg = "Unable to connect two areas from 'coord_from' {} to 'coord_to' {}, " \
                  "all allowed actions allocated".format(coord_from, coord_to[1:])
            raise ng.NeuGymConnectivityError(msg)

        if register_action is not None:
            if register_action not in self.actions:
                msg = "Illegal 'register_action' {}, expected one of {}".format(register_action, self.actions)
                raise ValueError(msg)
            if register_action not in free_actions:
                msg = "Unable to register action 'register_action' {}, already allocated".format(register_action)
                raise ng.NeuGymConnectivityError(msg)
            dx, dy = register_action
        else:
            dx, dy = free_actions[0]

        self.alias[tuple([coord_from[0]] + [coord_from[1] + dx] + [coord_from[2] + dy])] = coord_to
        self.alias[tuple([coord_to[0]] + [coord_to[1] - dx] + [coord_to[2] - dy])] = coord_from
        self.world.add_edge(coord_from, coord_to)

    def remove_path(self, coord_from, coord_to):
        if coord_from[0] == coord_to[0]:
            msg = "Not allowed to remove path within an area"
            raise ng.NeuGymPermissionError(msg)

        if (coord_from, coord_to) in list(nx.bridges(self.world)):
            msg = "Not allowed to remove path ({}, {}), world would be no longer connected".format(coord_from, coord_to)
            raise ng.NeuGymConnectivityError(msg)

        if len(coord_from) != 3 or len(coord_to) != 3:
            msg = "Tuple of length 3 expected for position coordinate"
            raise ValueError(msg)

        remove_list = []
        for action in self.actions:
            dx, dy = action
            alias_to = tuple([coord_from[0]] + [coord_from[1] + dx] + [coord_from[2] + dy])
            alias_from = tuple([coord_to[0]] + [coord_to[1] - dx] + [coord_to[2] - dy])

            if self.alias.get(alias_to) == coord_to and self.alias.get(alias_from) == coord_from:
                remove_list.append(alias_to)
                remove_list.append(alias_from)

        if len(remove_list) == 0:
            msg = "Inter-area path not found between {} and {}, noting to do".format(coord_from, coord_to)
            warnings.warn(RuntimeWarning(msg))
        else:
            assert len(remove_list) == 2
            for key in remove_list:
                self.alias.pop(key)
            self.world.remove_edge(coord_from, coord_to)

    def add_object(self, coord, reward, prob, punish=0):
        if coord in self.world.nodes:
            self.objects.append(_Object(reward, punish, prob, coord))
        else:
            msg = "Coordinate {} out of world".format(coord)
            raise ValueError(msg)

    def remove_object(self, coord):
        pop_idx = None
        for i, obj in enumerate(self.objects):
            if coord == obj.coord:
                pop_idx = i
                break
        if pop_idx is not None:
            self.objects.pop(pop_idx)
        else:
            msg = "No object found at {}".format(coord)
            raise ValueError(msg)

    def update_object(self, coord, **kwargs):
        for obj in self.objects:
            if coord == obj.coord:
                for key, value in kwargs.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
                    else:
                        msg = "'Object' object don't have attribute '{}', ignored.".format(key)
                        warnings.warn(RuntimeWarning(msg))
                return

        msg = "No object found at {}".format(coord)
        raise ValueError(msg)

    def set_altitude(self, area_idx, altitude_mat):
        if area_idx > self.num_area:
            msg = "Area {} not found".format(area_idx)
            raise ValueError(msg)

        area_shape = self.get_area_shape(area_idx)

        if altitude_mat.shape != area_shape:
            msg = "Mismatch shape between Area({}) {} and altitude matrix {}".format(area_idx,
                                                                                     area_shape,
                                                                                     altitude_mat.shape)
            raise ValueError(msg)

        altitude_mapping = {}

        for x in range(area_shape[0]):
            for y in range(area_shape[1]):
                coord = (area_idx, x, y)
                altitude_mapping[coord] = altitude_mat[x, y]
        nx.set_node_attributes(self.world, altitude_mapping, 'altitude')

    def get_area_shape(self, area_idx):
        if area_idx > self.num_area:
            msg = "Area {} not found".format(area_idx)
            raise ValueError(msg)

        max_x = 0
        max_y = 0
        for area, x, y in self.world.nodes:
            if area != area_idx:
                continue
            else:
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y
        return max_x + 1, max_y + 1

    def get_area_altitude(self, area_idx):
        if area_idx > self.num_area:
            msg = "Area {} not found".format(area_idx)
            raise ValueError(msg)

        area_shape = self.get_area_shape(area_idx)

        altitude_mat = np.zeros(area_shape)

        for coord in self.world.nodes:
            if coord[0] != area_idx:
                continue
            else:
                altitude_mat[coord[1], coord[2]] = nx.get_node_attributes(self.world, 'altitude')[coord]

        return altitude_mat

    def init_agent(self, init_coord=(0, 0, 0), overwrite=False):
        if not self.world.has_node(init_coord):
            msg = "Initial state coordinate {} out of world".format(init_coord)
            raise ValueError(msg)

        if self.agent is None or overwrite:
            self.agent = _Agent(init_coord)
        else:
            raise ng.NeuGymOverwriteError("Agent already exists, set 'overwrite=True' to overwrite")

    def step(self, action):
        if action not in self.actions:
            msg = "Illegal action {}, should be one of {}".format(action, self.actions)
            raise ValueError(msg)
        else:
            dx, dy = action

        done = False
        reward = 0
        current_state = self.agent.current_state
        next_state = (current_state[0], current_state[1] + dx, current_state[2] + dy)
        if not self.world.has_node(next_state):
            if next_state in self.alias.keys():
                next_state = self.alias[next_state]
            else:
                next_state = current_state

        altitude = nx.get_node_attributes(self.world, 'altitude')
        reward += altitude[current_state] - altitude[next_state]

        for obj in self.objects:
            if obj.coord == next_state:
                reward += obj.get_reward()
                done = True
                break

        self.time += 1
        if done:
            self.agent.reset()
        else:
            self.agent.update(current_state=next_state)

        return next_state, reward, done

    def set_reset_checkpoint(self, overwrite=False):
        if not self.has_reset_checkpoint or overwrite:
            for key in self.reset_state.keys():
                self.reset_state[key] = copy.deepcopy(getattr(self, key))
                self.has_reset_checkpoint = True
        else:
            raise ng.NeuGymOverwriteError("Reset state already exists, set 'overwrite=True' to overwrite")

    def reset(self):
        if not self.has_reset_checkpoint:
            raise ng.NeuGymCheckpointError("Reset state not found, use 'set_reset_state()' to set the reset checkpoint first")

        for key, value in self.reset_state.items():
            setattr(self, key, copy.deepcopy(value))

    def __repr__(self):
        msg = "GridWorld(\n" \
              "\ttime={}\n" \
              "\torigin=Origin([0])(shape={})\n".format(self.time, self.get_area_shape(0))

        if self.num_area == 0:
            msg += "\tareas=()\n"
        else:
            msg += "\tareas=(\n"
            for i in range(1, self.num_area + 1):
                msg += "\t\t[{}] Area(shape={})\n".format(i, self.get_area_shape(i))
            msg += "\t)\n"

        if len(self.objects) == 0:
            msg += "\tobjects=()\n"
        else:
            msg += "\tobjects=(\n"
            for i, obj in enumerate(self.objects):
                msg += "\t\t[{}] {}\n".format(i, str(obj))
            msg += "\t)\n"

        msg += "\tactions={}\n".format(self.actions)
        msg += "\tagent={}\n".format(str(self.agent))
        msg += "\thas_reset_state={}\n".format(self.has_reset_checkpoint)
        msg += ")"

        return msg
