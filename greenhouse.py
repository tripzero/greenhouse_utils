"""greenhouse.py"""

import math
import geothermal

earthSurfaceArea = 1.28 * math.pow(10,8) * 1000 #m^2 - area where earth meets sun
totalEarthArea = 510.1 * math.pow(10, 6) * 1000 #m^2

"earth mass at surface to 1m deep: "
earthMass = totalEarthArea * geothermal.ThermalConstants.Density.water

darkArea = totalEarthArea - earthSurfaceArea

solarConstant = 1362 #W/m^2

co2 = 400 #ppm

avgTemp = 0
gain = 1
loss = 0

while loss < gain:

	for second in range(86400 * 364):
	
		"assume the earth is full of water."

		earthEnergy = geothermal.energyCapacity(geothermal.ThermalConstants.SpecificHeat.water, earthMass, avgTemp)

		"estimate radiation loss for entire earth"

		loss = geothermal.radiantEnergy(geothermal.ThermalConstants.Emissivity.water, totalEarthArea, avgTemp)

		"add energy from the sun"
		gain = solarConstant * earthSurfaceArea

		earthEnergy -= loss
		earthEnergy += gain

		avgTemp = geothermal.temperature(geothermal.ThermalConstants.SpecificHeat.water, earthMass, earthEnergy)

		if second % 86400 == 0:
			print("day {0}".format(second / 86400))
			print("avgTemp = {0}".format(avgTemp))



