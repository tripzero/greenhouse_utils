import thermalobject
from thermalobject import ThermalConstants

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

air.temperature = 4
water.temperature = 9
soil.temperature = 9

time_to_transfer = 0

while air.temperature < soil.temperature - 1:
	soil.temperature = 9
	soil.transferTo(air, contactArea=soilContactArea, time=3600)
	time_to_transfer += 1

soil_time = time_to_transfer

print("Soil to air time: {}hrs".format(soil_time))

air.temperature = 4

time_to_transfer = 0

while air.temperature < water.temperature - 1:
	water.transferTo(air, contactArea = 12 * 6, time=3600)
	time_to_transfer += 1

print("Water to air time: {}hrs".format(time_to_transfer))
print("delta: {}".format(soil_time - time_to_transfer))
