import unittest
import numpy as np
import networkx as nx
from neugym.environment.gridworld import GridWorld


# Test GridWorld environment.
class TestGridWorldFunction(unittest.TestCase):
    def test_init(self):
        # Test default instantiation.
        w = GridWorld()
        self.assertEqual(w.get_area_altitude(0).all(), np.zeros((1, 1)).all())
        self.assertEqual(w.world.number_of_nodes(), 1)
        self.assertTrue((0, 0, 0) in w.world.nodes)

        # Test manually set origin shape.
        w = GridWorld((3, 3))
        self.assertEqual(w.get_area_altitude(0).all(), np.zeros((3, 3)).all())
        self.assertEqual(w.world.number_of_nodes(), 9)
        self.assertEqual(w.world.number_of_edges(), 12)

        # Test manually set origin altitude.
        altitude_mat = np.random.randn(3, 3)
        w = GridWorld((3, 3), origin_altitude_mat=altitude_mat)
        self.assertEqual(w.get_area_altitude(0).all(), altitude_mat.all())

        with self.assertRaises(ValueError):
            GridWorld((3, 3), origin_altitude_mat=np.zeros((3, 4)))

    def test_add_area(self):
        # Test 'add_area' function.
        # Test default parameters.
        w = GridWorld()
        w.add_area((2, 2))
        self.assertEqual(w.num_area, 1)
        self.assertTrue(((0, 0, 0), (1, 0, 0)) in w.world.edges)
        self.assertEqual(w.alias.get((0, 1, 0)), (1, 0, 0))
        self.assertEqual(w.alias.get((1, -1, 0)), (0, 0, 0))
        self.assertEqual(w.world.number_of_nodes(), 5)
        self.assertEqual(w.world.number_of_edges(), 5)
        self.assertEqual(w.get_area_altitude(1).all(), np.zeros((2, 2)).all())

        # Test manually specify inter-area connections.
        with self.assertRaises(ValueError):
            w.add_area((2, 3), access_from=(2, 1, 1), access_to=(1, 0), register_action=(0, 1))
        with self.assertRaises(ValueError):
            w.add_area((2, 3), access_from=(1, 1, 1), access_to=(1, 2))
        self.assertEqual(w.num_area, 1)
        self.assertEqual(list(w.world.nodes), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)])

        w.add_area((2, 3), access_from=(1, 1, 1), access_to=(1, 0), register_action=(0, 1))
        self.assertEqual(w.num_area, 2)
        self.assertTrue(((1, 1, 1), (2, 1, 0)) in w.world.edges)
        self.assertEqual(w.alias.get((1, 1, 2)), (2, 1, 0))
        self.assertEqual(w.alias.get((2, 1, -1)), (1, 1, 1))
        self.assertEqual(len(w.alias), 4)
        with self.assertRaises(ValueError):
            w.add_area((3, 3), access_from=(0, 0))
        with self.assertRaises(ValueError):
            w.add_area((3, 3), access_from=(99, 0, 0))

        with self.assertRaises(ValueError):
            w.add_area((3, 3), access_to=(0, 0, 0))
        with self.assertRaises(ValueError):
            w.add_area((3, 3), access_to=(3, 3))
        with self.assertRaises(ValueError):
            w.add_area((3, 3), access_to=(1, 1))
        with self.assertRaises(ValueError):
            w.add_area((3, 3), access_from=(2, 1, 2), access_to=(1, 0), register_action=(1, 0))
        with self.assertRaises(ValueError):
            w.add_area((3, 3), access_from=(2, 1, 2), access_to=(1, 0), register_action=(3, 3))

        # Test add area with altitude.
        w = GridWorld()
        altitude_mat = np.random.rand(3, 5)
        w.add_area((3, 5), altitude_mat=altitude_mat)
        self.assertEqual(w.get_area_altitude(1).all(), altitude_mat.all())
        with self.assertRaises(ValueError):
            w.add_area((3, 3), altitude_mat=np.zeros((2, 2)))
        self.assertEqual(w.num_area, 1)
        # Test if all position have attribute 'altitude'.
        self.assertEqual(len(nx.get_node_attributes(w.world, 'altitude')), 16)

    def test_remove_area(self):
        # Test 'remove_area' function.
        w = GridWorld()
        w.add_area((2, 2))
        w.add_area((3, 3), access_from=(1, 1, 1))
        w.add_area((5, 5))
        w.add_object((1, 0, 0), 1, 0.5)
        w.add_object((2, 0, 0), 1, 0.6)
        w.add_object((3, 1, 1), 1, 0.7)
        self.assertEqual(w.world.number_of_edges(), 59)
        self.assertTrue(((1, 1, 1), (2, 0, 0)) in w.world.edges)
        self.assertEqual(w.alias.get((1, 2, 1)), (2, 0, 0))
        self.assertTrue(((0, 0, 0), (3, 0, 0)) in w.world.edges)

        # Test remove "bridge" area.
        with self.assertRaises(RuntimeError):
            w.remove_area(1)

        w.remove_area(2)
        self.assertEqual(w.num_area, 2)
        self.assertEqual(w.world.number_of_nodes(), 30)
        self.assertEqual(w.world.number_of_edges(), 46)
        self.assertTrue(((1, 1, 1), (2, 0, 0)) not in w.world.edges)
        self.assertTrue((2, -1, 0) not in w.alias.keys())
        self.assertEqual(w.alias.get((0, 0, 1)), (2, 0, 0))
        self.assertTrue(w.alias.get((2, 0, -1)), (0, 0, 0))
        self.assertEqual(len(w.alias), 4)
        self.assertEqual(len(w.objects), 2)
        for obj in w.objects:
            self.assertTrue(obj.coord != (2, 0, 0))

        w.add_area((5, 5), access_to=(4, 4))
        w.add_object((3, 1, 1), 1, 0.7)
        w.remove_area(1)
        w.remove_area(1)
        self.assertEqual(w.num_area, 1)
        self.assertEqual(w.world.number_of_nodes(), 26)
        self.assertEqual(w.world.number_of_edges(), 41)
        self.assertTrue(((0, 0, 0), (1, 0, 0)) not in w.world.edges)
        self.assertTrue(((0, 0, 0), (1, 4, 4)) in w.world.edges)
        self.assertEqual(len(w.objects), 1)
        self.assertEqual((1, 1, 1), w.objects[0].coord)
        self.assertTrue((1, 1, 1) in w.world.nodes)
        self.assertEqual(len(w.alias), 2)
        self.assertEqual(w.alias.get((0, -1, 0)), (1, 4, 4))
        self.assertEqual(w.alias.get((1, 5, 4)), (0, 0, 0))

        # Test remove origin.
        with self.assertRaises(ValueError):
            w.remove_area(0)

    def test_add_path(self):
        # Test 'add_path' function.
        w = GridWorld()

        # Test add self-loop at origin.
        with self.assertRaises(ValueError):
            w.add_path((0, 0, 0), (0, 0, 0))

        w.add_area((2, 2))
        w.add_area((3, 3))
        w.add_area((2, 2), access_to=(1, 1))
        with self.assertRaises(ValueError):
            w.add_path((1, 1, 1), (2, 0))
        with self.assertRaises(ValueError):
            w.add_path((1, 1, 1), (2, 2, 0), (-1, 0))
        w.add_path((1, 1, 1), (2, 2, 0))
        self.assertEqual(w.alias.get((1, 1, 2)), (2, 2, 0))
        self.assertEqual(w.alias.get((2, 2, -1)), (1, 1, 1))
        self.assertTrue(((1, 1, 1), (2, 2, 0)) in w.world.edges)

        # Test add multiple paths between two positions.
        w.add_path((1, 1, 0), (2, 0, 2))
        with self.assertRaises(ValueError):
            w.add_path((1, 1, 0), (2, 0, 2))

    def test_remove_path(self):
        # Test 'remove_path' function.
        w = GridWorld()
        w.add_area((2, 4))
        with self.assertRaises(ValueError):
            w.remove_path((0, 0, 0), (1, 0, 0))
        w.add_area((3, 5))
        w.add_path((1, 1, 0), (2, 0, 4))
        with self.assertRaises(ValueError):
            w.add_path((1, 1, 0), (2, 0, 4))
        self.assertEqual(len(w.alias), 6)
        with self.assertWarns(UserWarning):
            w.remove_path((1, 1, 3), (0, 0, 0))
        with self.assertRaises(ValueError):
            w.remove_path((0, 0), (1, 1, 1))
        w.remove_path((1, 1, 0), (2, 0, 4))
        self.assertEqual(len(w.alias), 4)
        self.assertTrue(((1, 1, 0), (2, 0, 4)) not in w.world.edges)

        # Test remove path within an area.
        with self.assertRaises(ValueError):
            w.remove_path((1, 0, 0), (1, 1, 0))

    def test_add_object(self):
        # Test 'add_object' function.
        w = GridWorld()
        w.add_area((2, 2))
        w.add_area((4, 3))

        w.add_object((1, 1, 1), 1, 0.3)
        w.add_object((2, 2, 1), 1, 0.7, -1)
        self.assertEqual(len(w.objects), 2)
        self.assertEqual(w.objects[0].reward, 1)
        self.assertEqual(w.objects[0].prob, 0.3)
        self.assertEqual(w.objects[0].punish, 0)
        self.assertEqual(w.objects[0].coord, (1, 1, 1))
        self.assertEqual(w.objects[1].punish, -1)

        # Test add object with illegal coordinate.
        with self.assertRaises(ValueError):
            w.add_object((1, 1), 1, 0, 0.5)
        with self.assertRaises(ValueError):
            w.add_object((3, 1, 1), 1, 0, 0.5)

    def test_remove_object(self):
        # Test 'remove_object' function.
        w = GridWorld()
        w.add_area((4, 3))
        w.add_area((4, 3))
        w.add_area((4, 3), access_to=(3, 1))
        w.add_object((1, 2, 1), 1, 0.2)
        w.add_object((2, 2, 1), 1, 0.8)
        w.add_object((3, 2, 1), 1, 0.9)

        w.remove_object((3, 2, 1))
        self.assertEqual(len(w.objects), 2)
        for obj in w.objects:
            self.assertTrue(obj.coord != (3, 2, 1))

        # Test remove undefined object.
        with self.assertRaises(ValueError):
            w.remove_object((0, 0, 0))

    def test_update_object(self):
        # Test 'update_object' function.
        w = GridWorld()
        w.add_area((4, 3))
        w.add_area((4, 3))
        w.add_object((1, 2, 1), 1, 0.3)
        w.add_object((2, 2, 1), 1, 0.7)

        w.update_object((1, 2, 1), reward=10, prob=0.2, punish=-10)
        self.assertEqual(w.objects[0].reward, 10)
        self.assertEqual(w.objects[0].prob, 0.2)
        self.assertEqual(w.objects[0].punish, -10)

        # Test modify undefined object.
        with self.assertRaises(ValueError):
            w.update_object((0, 0, 0), reward=1)

        # Test modify illegal attribute.
        with self.assertWarns(UserWarning):
            w.update_object((1, 2, 1), reward=1, prob=0.3, punish=0, undefined_attr=10)

    def test_set_altitude(self):
        # Test 'set_altitude' function.
        w = GridWorld()
        w.add_area((3, 4))
        self.assertEqual(w.get_area_altitude(1).all(), np.zeros((3, 4)).all())
        altitude_mat = np.random.randn(3, 4)
        w.set_altitude(1, altitude_mat=altitude_mat)
        self.assertEqual(w.get_area_altitude(1).all(), altitude_mat.all())
        with self.assertRaises(ValueError):
            w.set_altitude(2, altitude_mat=altitude_mat)
        with self.assertRaises(ValueError):
            w.set_altitude(1, np.zeros((2, 2)))

    def test_get_area_shape(self):
        # Test 'get_area_shape' function.
        w = GridWorld()
        w.add_area((4, 10))
        w.add_area((4, 3))

        self.assertEqual(w.get_area_shape(0), (1, 1))
        self.assertEqual(w.get_area_shape(2), (4, 3))

        with self.assertRaises(ValueError):
            w.get_area_shape(3)

    def test_get_area_altitude(self):
        # Test 'get_area_altitude' function.
        w = GridWorld()
        altitude_mat = np.random.randn(5, 8)
        w.add_area((5, 8), altitude_mat=altitude_mat)
        self.assertEqual(w.get_area_altitude(1).all(), altitude_mat.all())
        with self.assertRaises(ValueError):
            w.get_area_altitude(2)

    def test_init_agent(self):
        # Test 'add_agent' function.
        w = GridWorld()
        with self.assertRaises(ValueError):
            w.init_agent((2, 2, 2))
        w.init_agent()
        self.assertEqual(w.agent._init_state, (0, 0, 0))
        with self.assertRaises(RuntimeError):
            w.init_agent()

        # Test initialize agent at other positions.
        w = GridWorld()
        w.add_area((2, 2))
        w.init_agent((1, 1, 0))
        self.assertEqual(w.agent._init_state, (1, 1, 0))

    def test_step(self):
        pass

    def test_set_init_state(self):
        pass

    def test_reset(self):
        pass


class TestGridWorldBuild(unittest.TestCase):
    def test_build(self):
        pass


if __name__ == '__main__':
    unittest.main()