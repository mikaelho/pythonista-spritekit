import ui
from spritekit import *
import pygestures
import scripter

class ListScene(Scene, pygestures.GestureMixin):
  
  def __init__(self, **kwargs):
    super().__init__(physics=UIPhysics, edges=True, **kwargs)
    self.anchor_point = (0,1)
    
  def update(self, ct):
    for node in self.children:
      if node.dynamic:
        view_pos = self.convert_to_view(node.position)
        if node.view.center != view_pos:
          if node.view.animation is not None:
            scr = scripter.find_scripter_instance()
            scr.cancel(node.view.animation)
          node.animation = scripter.center_to(node.view, view_pos, duration=0.1)

    
class PhysicalView(ui.View):
  
  def __init__(self, scene, **kwargs):
    super().__init__(**kwargs)
    self.scene = scene
    _,_,w,h = self.frame
    x,y = scene.convert_from_view(self.center)
    self.node = BoxNode((w,h), position=(x,y) , parent=scene)
    self.animation = None
    self.node.constraints.append(Constraint.position_y(Range.upper(-30)))
    self.node.view = self
    
  def touch_began(self, t):
    self.node.dynamic = False
    #self.start_point = ui.convert_point(t.location, from_view=self, to_view=self.superview)
    
  def touch_moved(self, t):
    point = ui.convert_point(t.location, from_view=self, to_view=self.superview)
    prev_point = ui.convert_point(t.prev_location, from_view=self, to_view=self.superview)
    delta = point - prev_point
    self.center += delta
    self.node.position = scene.convert_from_view(self.center)
    
  def touch_ended(self, t):
    self.node.dynamic = True
    
class UINode(BoxNode):
  
  def __init__(self, view, **kwargs):
    super().__init__(**kwargs)
    self.view = view
    
    
scene = ListScene()

v = scene.view
listview = ui.View(frame=scene.view.bounds,
  flex='WH', background_color='black')
v.add_subview(listview)

v1 = PhysicalView(scene,
  frame=(100,100,200,50),
  background_color='blue'
)
v.add_subview(v1)

v2 = PhysicalView(scene,
  frame=(100,300,200,50),
  background_color='red'
)
v.add_subview(v2)

v3 = PhysicalView(scene,
  frame=(100,300,200,50),
  background_color='green'
)
v.add_subview(v3)

v4 = PhysicalView(scene,
  frame=(100,300,200,50),
  background_color='orange'
)
v.add_subview(v4)

#listview.hidden = True

run(scene)
