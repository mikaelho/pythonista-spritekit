import ui
from spritekit import *
import pygestures
import scripter

class ListScene(Scene, pygestures.GestureMixin):
  
  def __init__(self, **kwargs):
    super().__init__(physics=UIPhysics, edges=True, **kwargs)
    self.anchor_point = (0,1)
    print(self.node.physicsBody())
    
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
  
  def __init__(self, scene, margin=8, **kwargs):
    super().__init__(**kwargs)
    self.scene = scene
    _,_,w,h = self.frame
    x,y = scene.convert_from_view(self.center)
    self.node = BoxNode((w+margin,h+margin), position=(x,y) , parent=scene)
    self.animation = None
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
    
class ListView(ui.View):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.items = [
      PhysicalView(scene,
        frame=(100,100,200,50),
        background_color='red'
      ),
      PhysicalView(scene,
        frame=(100,101,200,50),
        background_color='green'
      ),
      PhysicalView(scene,
        frame=(100,102,200,50),
        background_color='blue'
      ),
      PhysicalView(scene,
        frame=(100,103,200,50),
        background_color='orange'
      )
    ]
    for v in self.items:
      self.add_subview(v)
    self.update_constraints()
    
  def update_constraints(self):
    return 
    for i, v in enumerate(self.items):
      constraints = [
        Constraint.position_x(Range.constant(150))
      ]
      '''
      if v != self.items[-1]:
        constraints.append(
          Constraint.distance_to_node(self.items[i+1].node, Range.constant(66))
        )
      if i == 0:
        constraints.append(
          Constraint.position_y(Range.upper(-50))
        )
      else:
        constraints.append(
          Constraint.distance_to_node(self.items[i-1].node, Range.constant(66))
        )
      '''

      v.node.constraints = constraints
        
    
scene = ListScene()

v = scene.view
listview = ListView(frame=scene.view.bounds,
  flex='WH', background_color='black')
v.add_subview(listview)

#listview.hidden = True

run(scene, 'full_screen', hide_title_bar=True)
