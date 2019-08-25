from spritekit import *
import ui, math, random
import vector

top_alt = 0
range_down = 200
step = 100

strtlvl = top_alt-range_down/2

points = [(-step,0), (-step,strtlvl), (0, strtlvl), (step,strtlvl)]

for i in range(2, 20):
  points.append((
    i*step,
    random.randint(top_alt-range_down, top_alt)
  ))
  
points += [(20*step,strtlvl), (21*step, strtlvl), (21*step, 0), (-step,0)]

class ScrollingScene(Scene):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.camera = CameraNode(parent=self)
    
  def update(self, ct):
    pass
    

scene = Scene(anchor_point=(0.5,0.5))

PointsNode(points, smooth=True,
fill_color='seagreen',
affected_by_gravity=False,
linear_damping=0.0,
parent=scene)

c = CameraNode(velocity=(100,0), parent=scene)

run(scene)
