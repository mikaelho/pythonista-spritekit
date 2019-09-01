import ui
from spritekit import *
from random import random

class DrawView(ui.View):
  
  def __init__(self, scene, **kwargs):
    super().__init__(**kwargs)
    self.scene = scene
    self.points = []
    self.relative_points = []
    self.start = None
    self.background_color = (1,1,1,0.000000001)
    
    self.every_other = False
  
  def touch_began(self, t):
    self.points = []
    self.relative_points = []
    self.start = t.location

  def touch_moved(self, t):
    self.points.append(t.location)
    relative = t.location-self.start
    self.relative_points.append((relative.x, -relative.y))
    self.set_needs_display()
    
  def touch_ended(self, t):
    self.every_other = self.every_other == False
    ShapeNode(self.relative_points,
      hull=self.every_other,
      line_color=(random(),random(),random()),
      line_width=3,
      position=self.scene.convert_from_view(self.start),
      parent=self.scene)
    self.points = []
    self.start = None
    self.set_needs_display()
    
  def draw(self):
    if self.start is None: return 
    path = ui.Path()
    path.move_to(*self.start)
    for p in self.points:
      path.line_to(*p)
    ui.set_color('white')
    #path.line_width = 1
    path.stroke()
    

class DrawScene(Scene):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.anchor_point = (0.5, 0)
    BoxNode((250,20),
      fill_color='black',
      position=(0, 50),
      dynamic=False,
      parent=self
    )
    
  def update(self, ct):
    for node in self.children:
      if node.position.y < 0:
        node.parent = None

scene = DrawScene()

v = scene.view
draw = DrawView(scene, frame=v.bounds, flex='WH')
v.add_subview(draw)

run(scene)
