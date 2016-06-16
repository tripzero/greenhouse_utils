import thermalobject
import sys

def status(msg):
	sys.stdout.write('\x1b[2K\x1b[80D')
	sys.stdout.write('\x1b[1D')
	sys.stdout.write(msg)
	#sys.stdout.flush()

water_d = (6.096, 0.6096, 0.0762)
soil_d = (6.096, 3.048, 2.4384)
air_d = (6.096, 3.048, 2.4384)

radiator_d = (0.681, 0.6048, 0.2016)

water = thermalobject.Water(water_d)
soil = thermalobject.Soil(soil_d)
air = thermalobject.Air(air_d, 40)
radiator = thermalobject.Aluminum(radiator_d)


print("starting energy:")
print("water :", water.energy)
print("soil :", soil.energy)
print("air: ", air.energy)


def airToSoil(air, soil):
	seconds = 0

	print("")
	print("transfering air to soil...")

	while round(soil.temperature,0) < round(air.temperature,0) - 1:

		air.transferTo(soil)
		#status("air energy: {}, air temp {}, soil energy: {}, soil temp: {}".format(air.energy, air.temperature, soil.energy, soil.temperature))
		seconds += 1

	print("time to transfer air energy to soil: {}hrs".format(seconds/3600.0))



def airToWater(air, water, soil):
	#reset:
	air.temperature = 40
	soil.temperature = 15
	seconds = 0

	print("")
	print("transfering air to water...")

	while round(water.temperature, 0) < round(air.temperature, 0) - 1:

		air.transferTo(soil)
		soil.transferTo(water)
		air.transferTo(radiator)
		radiator.transferTo(water)
		seconds += 1

	print("time to transfer air energy to water: {}hrs".format(seconds/3600.0))


from multiprocessing import Process

a = Process(target=airToSoil, args=(air, soil))

air = thermalobject.Air(air_d, 40)

b = Process(target=airToWater, args=(air, water, soil))

a.start()
b.start()

a.join()
b.join()
