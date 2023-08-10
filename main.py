from tmxpy import convertMapNameToFile, TMXpy
from pathlib import Path
import json, os
from PIL import Image
from typing import cast

MAP_PATH = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Stardew Valley\\Content (unpacked)\\Maps'
IGNORE = ['VolcanoEntrance']

if not os.path.exists("output"):
    os.mkdir("output")

Farm = TMXpy(
    [Path(MAP_PATH), Path.joinpath(Path(os.getcwd()), "sheets")],
    path=Path.joinpath(Path(MAP_PATH), "Farm.tmx")
)

Farm.generateGIDDict()
Farm.addTilesheet("warp_tilesheet", "WarpTilesheet", {})

Farm.generateGIDDict()

Farm_warps = Farm.parseWarps()

img = Image.new("RGBA", (Farm.tmxDimensions[0] * 16, Farm.tmxDimensions[1] * 16), (0, 0, 0, 0))
data = {}
#warps = {}

#imgs['Farm'] = Farm.renderAllLayers("Paths")
#warps['Farm'] = Farm_warps
data['Farm'] = {
    "img": Farm.renderAllLayers(["Paths"]),
    "warps": Farm_warps
}

def loopWarps(map_warps, map, mapName):
    print(f"Looping warps for {mapName}")

    for warp in map_warps:
        x = warp["map_x"]
        y = warp["map_y"]
        if warp["map_x"] < 0:
            x = 1
        elif warp["map_x"] > map.tmxDimensions[0] -1:
            x = map.tmxDimensions[0] - 1
        
        if warp["map_y"] < 0:
            y = 1
        elif warp["map_y"] > map.tmxDimensions[1] -1:
            y = map.tmxDimensions[1] - 1


        print(warp, x, y, map.tmxDimensions)
        #print(Farm.maxGID)

        """
        map.setTile(
            x,
            y,
            str(Farm.maxGID),
            layerName="Front"
        )
        """
        fp = convertMapNameToFile(warp["destination"])

        
        if warp["destination"] in data or warp["destination"] in IGNORE:
            continue
        
        Destination = TMXpy(
            [Path(MAP_PATH), Path.joinpath(Path(os.getcwd()), "sheets")],
            path=Path.joinpath(Path(MAP_PATH), fp + ".tmx")
        )



        Destination.generateGIDDict()
        Destination_warps = Destination.parseWarps()
        #imgs[warp["destination"]] = Destination.renderAllLayers("Paths")
        #warps[warp["destination"]] = Destination_warps
        if os.path.exists(f'output/{warp["destination"]}.png'):
            i = Image.open(f'output/{warp["destination"]}.png')
        else:
            i = Destination.renderAllLayers(["Paths"])
        data[warp["destination"]] = {
            "img": i,
            "warps": Destination_warps
        }

        loopWarps(Destination_warps, Destination, warp["destination"])

loopWarps(Farm_warps, Farm, "Farm")

print("Saving images...")
for imgName in data:
    data[imgName]["img"].save(f"output/{imgName}.png")

#figure out how wide it would be if we joined them all together, as well as how tall it would be if we joined together where the warps are
#then create a new image with those dimensions
#then loop through the images and paste them into the new image
#then save the new image
newWidth = 0
newHeight = 0

#palce each image in the new image, and connectthem with the warps, and save it
for imgName in data:
    newWidth += data[imgName]["img"].width
    newHeight += data[imgName]["img"].height

print(newWidth, newHeight)

newImg = Image.new("RGBA", (newWidth, newHeight), (0, 0, 0, 0))

midpoint = (int(newWidth / 2), int(newHeight / 2))

covered_maps = []

offsets = {
    'BusStop': (
        0, #positive is right, negative is left
        16), #positive is down, negative is up
    'Railroad': (16, 0),
}

def loop():
    for imgName in data:
        print(imgName, covered_maps)

        data[imgName]["bounds"] = {
            "tl": (0, 0),
            "tr": (data[imgName]["img"].width, 0),
            "bl": (0, data[imgName]["img"].height),
            "br": (data[imgName]["img"].width, data[imgName]["img"].height)
        }

        data[imgName]["midpoint"] = (data[imgName]["img"].width / 2, data[imgName]["img"].height / 2)

        if len(covered_maps) == 0:
            newImg.paste(data[imgName]["img"], midpoint)
            covered_maps.append(imgName)

        if "coords" not in data[imgName]:
            data[imgName]["coords"] = {
                "tl": midpoint, #top left
                "tr": (midpoint[0] + data[imgName]["img"].width, midpoint[1]), #top right
                "bl": (midpoint[0], midpoint[1] + data[imgName]["img"].height), #bottom left
                "br": (midpoint[0] + data[imgName]["img"].width, midpoint[1] + data[imgName]["img"].height) #bottom right
            }

        wtimage = Image.open("sheets/warp_tilesheet.png")

        for warp in data[imgName]["warps"]:
            if warp["destination"] in covered_maps or warp["destination"] in IGNORE:
                continue

            data[warp["destination"]]["img"].paste(wtimage, (warp["dest_x"] * 16, warp["dest_y"] * 16))

            top_left = data[imgName]["coords"]["tl"]
            
            #find the location of the source warp on the destination image
            dest_abs_coords = {
                "x": int(top_left[0] + (warp["map_x"] * 16)),
                "y": int(top_left[1] + (warp["map_y"] * 16))
            }
            
            if warp["destination"] in offsets:
                dest_abs_coords["x"] += offsets[warp["destination"]][0]
                dest_abs_coords["y"] += offsets[warp["destination"]][1]

            dest_img_box_coords = (
                dest_abs_coords["x"] - (warp["dest_x"] * 16),
                dest_abs_coords["y"] - (warp["dest_y"] * 16)
            )

                

            print(f'Pasting {warp["destination"]} at {dest_img_box_coords}')
            newImg.paste(data[warp["destination"]]["img"], dest_img_box_coords)



            covered_maps.append(warp["destination"])

            
            data[warp["destination"]]["coords"] = {
                "tl": dest_img_box_coords,
                "tr": (dest_img_box_coords[0] + data[warp["destination"]]["img"].width, dest_img_box_coords[1]), # type: ignore
                "bl": (dest_img_box_coords[0], dest_img_box_coords[1] + data[warp["destination"]]["img"].height), # type: ignore
                "br": (dest_img_box_coords[0] + data[warp["destination"]]["img"].width, dest_img_box_coords[1] + data[warp["destination"]]["img"].height) # type: ignore
            }
            
        
        
loop()

for imgName in data:
    data[imgName]["img"].save(f"output/{imgName}_2.png")

newImg.save("output/combined.png")



"""for imgName in data:
        print(imgName, covered_maps)
        if imgName in covered_maps:
            continue

        data[imgName]["bounds"] = {
            "tl": (0, 0),
            "tr": (data[imgName]["img"].width, 0),
            "bl": (0, data[imgName]["img"].height),
            "br": (data[imgName]["img"].width, data[imgName]["img"].height)
        }

        data[imgName]["origin"] = (data[imgName]["img"].width / 2, data[imgName]["img"].height / 2)
        if "coords" not in data[imgName]:
            data[imgName]["coords"] = {
                "tl": (data[imgName]["origin"][0] - origin[0], data[imgName]["origin"][1] - origin[1]), #top left
                "tr": (data[imgName]["origin"][0] + origin[0], data[imgName]["origin"][1] - origin[1]), #top right
                "bl": (data[imgName]["origin"][0] - origin[0], data[imgName]["origin"][1] + origin[1]), #bottom left
                "br": (data[imgName]["origin"][0] + origin[0], data[imgName]["origin"][1] + origin[1]) #bottom right
            }

        if len(covered_maps) == 0:
            newImg.paste(data[imgName]["img"], origin) # type: ignore
            covered_maps.append(imgName)


        #check if it touches any other maps
        for warp in data[imgName]["warps"]:
            if warp["destination"] in covered_maps:
                continue

            top_left = data[imgName]["coords"]["tl"]
            #minus the coordinates of the warp on the destination image
            src_x = warp["map_x"] if warp["map_x"] > 0 else 0
            src_y = warp["map_y"] if warp["map_y"] > 0 else 0

            # print(f'Warp: {warp["destination"]}, Map X: {src_x}, Map Y: {src_y} | Top Left: {top_left}')
            # print(f'Coords: {data[imgName]["coords"]}')
            img_src_x = int(top_left[0] + src_x * 16)
            img_src_y = int(top_left[1] + src_y * 16)

            print(
                f'Warp: {warp["destination"]}, Map X: {src_x}, Map Y: {src_y} | Top Left: {top_left} | Image X: {img_src_x}, Image Y: {img_src_y}'
            )


            

            warp_coords = {
                "x": 1 - 1,
                "y": 2 - 1,
            }


            box_coords = (
                warp_coords['x'],
                warp_coords['y']
            )

            print(warp_coords, box_coords)

            print(f'Pasting {warp["destination"]} at {box_coords}')
            #paste the image at the right spot
            # newImg.paste(data[warp["destination"]]["img"], box_coords)
            data[warp["destination"]]["coords"] = {
                "tl": box_coords,
                "tr": (warp_coords['x'] + data[warp["destination"]]["img"].width, warp_coords['y']), # type: ignore
                "bl": (warp_coords['x'], warp_coords['y'] + data[warp["destination"]]["img"].height), # type: ignore
                "br": (warp_coords['x'] + data[warp["destination"]]["img"].width, warp_coords['y'] + data[warp["destination"]]["img"].height) # type: ignore
            }

            print(f'Coords: {data[warp["destination"]]["coords"]}')
            newImg.paste(data[warp["destination"]]["img"], data[warp["destination"]]["coords"]["tl"])


            covered_maps.append(warp["destination"])
"""

'''
map_top_left = data[imgName]["coords"]["tl"]

            print(f'Warp: {warp["destination"]}, Map X: {warp["map_x"]}, Map Y: {warp["map_y"]} | Top Left: {map_top_left}')

            reversed_dest_x = data[warp["destination"]]["img"].width - warp["dest_x"] * 16
            reversed_dest_y = data[warp["destination"]]["img"].height - warp["dest_y"] * 16

            #calculate the position of the warp's map_x and map_y on the new image based on map_top_left
            warp_abs_coords = {
                "x": map_top_left[0] + (warp["map_x"] * 16),
                "y": map_top_left[1] + (warp["map_y"] * 16)
            }

            print(f'Warp: {warp["destination"]}, Map X: {warp["map_x"]}, Map Y: {warp["map_y"]} | Abs Coords: {warp_abs_coords}')
            print(f'^^ | Reversed Dest X: {reversed_dest_x}, Reversed Dest Y: {reversed_dest_y}')

            dest_abs_coords = {
                "x": int(warp_abs_coords["x"] + (reversed_dest_x * 16)),
                "y": int(warp_abs_coords["y"] + (reversed_dest_y * 16))
            }

            dest_img_box_coords = (
                dest_abs_coords["x"],
                dest_abs_coords["y"]
            )

            print(f'Pasting {warp["destination"]} at {dest_img_box_coords}')

            newImg.paste(data[warp["destination"]]["img"], dest_img_box_coords)
            covered_maps.append(warp["destination"])
            
'''
'''
            dest_abs_coords = {
                "x": int(top_left[0] + (src_rel_x * 16)),
                "y": int(top_left[1] + (src_rel_y * 16))
            }

            dest_img_box_coords = (
                dest_abs_coords["x"],
                dest_abs_coords["y"]
            )

            this works, but it puts the top left of the destination at the warp, instead put the destination warp at the source warp
            '''