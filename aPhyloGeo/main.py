from aPhyloGeo.aPhyloGeo import geneticPipeline, climaticPipeline
from aPhyloGeo.Params import Params

titleCard = r"""
        ____    __               ___           ____
       /\  _`\ /\ \             /\_ \         /\  _`\
   __  \ \ \L\ \ \ \___   __  __\//\ \     ___\ \ \L\_\     __    ___
 /'__`\ \ \ ,__/\ \  _ `\/\ \/\ \ \ \ \   / __`\ \ \L_L   /'__`\ / __`\
/\ \L\.\_\ \ \/  \ \ \ \ \ \ \_\ \ \_\ \_/\ \L\ \ \ \/, \/\  __//\ \L\ \
\ \__/.\_\\ \_\   \ \_\ \_\/`____ \/\____\ \____/\ \____/\ \____\ \____/
 \/__/\/_/ \/_/    \/_/\/_/`/___/> \/____/\/___/  \/___/  \/____/\/___/
                              /\___/
                              \/__/
"""  # https://patorjk.com/software/taag/#p=display&f=Larry%203D&t=aPhyloGeo%20

if __name__ == "__main__":
    print(titleCard + "\n")
    p = Params()
    climaticTrees = climaticPipeline(p.file_name, p.names)
    geneticPipeline(climaticTrees, p)
