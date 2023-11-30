from tmxpy import convertMapNameToFile, TMXpy
from pathlib import Path
import json, os
from PIL import Image
from typing import cast

MAP_PATH = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Stardew Valley\\Content (unpacked)\\Maps'
IGNORE = ['VolcanoEntrance']

if not os.path.exists("output"):
    os.mkdir("output")

def main(inputMapName: str = 'Farm.tmx', inputPath: str | None | Path = None):
    if inputPath != None:
        inputPath = Path.joinpath(Path(MAP_PATH), inputMapName)
    else:
        inputPath = os.getcwd() + '\\' + inputMapName
    Start = TMXpy(
        [Path(MAP_PATH), Path.joinpath(Path("./sheets"))],
        path=Path(str(inputPath))
    )

    Start.generateGIDDict()
    Start.addTilesheet("warp_tilesheet", "WarpTilesheet", {})

    Start.generateGIDDict()

    Start_warps = Start.parseWarps()

    img = Image.new("RGBA", (Start.tmxDimensions[0] * 16, Start.tmxDimensions[1] * 16), (0, 0, 0, 0))
    data = {}
    #warps = {}

    #imgs['Start'] = Start.renderAllLayers("Paths")
    #warps['Start'] = Start_warps
    data[inputMapName.replace('.tmx', '')] = {
        "img": Start.renderAllLayers(["Paths"]),
        "warps": Start_warps
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
            #print(Start.maxGID)

            """
            map.setTile(
                x,
                y,
                str(Start.maxGID),
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

    loopWarps(Start_warps, Start, "Start")

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

    newImg = newImg.crop(newImg.getbbox())

    newImg.save("output/combined.png")


if __name__ == '__main__':
    main('Farm.tmx')