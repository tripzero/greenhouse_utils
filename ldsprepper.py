import thermalobject
from thermalobject import ThermalConstants

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--air", help="starting air temperature", default=0, type=int)

args = parser.parse_args()

air_volume = 204
airMass = air_volume * ThermalConstants.Density.air
air = thermalobject.Air(mass=airMass)

waterMass = 114 * 20 * 1000
water = thermalobject.Water(mass=waterMass)

"40ft x 20ft x 8ft deep"
soilMass = ThermalConstants.Density.soil * 12 * 6 * 2.4

"length of tube * circumference of tube.  Tube length is 82m.  Tube radius 0.0508m"
soilContactArea = 26

soil = thermalobject.Soil(mass=soilMass)

"set temperatures"

air.temperature = args.air
water.temperature = 9
soil.temperature = 9

time_to_transfer = 0

def energy_balance(a, b):
	heating = a.temperature < b.temperature

	if heating:
		return a.temperature < b.temperature - 1
	else:
		return a.temperature > b.temperature + 1


while energy_balance(air, soil):
	soil.transferTo(air, contactArea=soilContactArea, time=3600)
	time_to_transfer += 1

soil_time = time_to_transfer

print("Soil to air time: {}hrs".format(soil_time))
print("Final soil temperature: {}".format(soil.temperature))

air.temperature = args.air

time_to_transfer = 0

while energy_balance(air, water):
	water.transferTo(air, contactArea = 12 * 6, time=3600)
	time_to_transfer += 1

print("Water to air time: {}hrs".format(time_to_transfer))
print("delta: {}".format(soil_time - time_to_transfer))
print("Final water temperature: {}".format(water.temperature))
