import unittest
from data_ingestion import calculate_cost, MaterialProfile, GeometryConfig

class TestDataIngestion(unittest.TestCase):

    def test_calculate_cost(self):
        # Create sample material and geometry
        material = MaterialProfile(
            material_id="Aluminum",
            thermal_conductivity=0.1,
            emissivity=0.2,
            specific_heat=0.3,
            density=0.4
        )
        geometry = GeometryConfig(
            geometry_id="flat_plate",
            surface_area=1.0,
            thickness=0.01,
            inclination_angle=0.0
        )

        # Calculate cost
        cost = calculate_cost([material], geometry)

        # Assert that the cost is positive
        self.assertGreater(cost, 0)

if __name__ == '__main__':
    unittest.main()