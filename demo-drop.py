from spritekit import *
from random import *

class DropScene(Scene):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.anchor_point = (0.5, 0)
    BoxNode((275,20),
      fill_color='black',
      position=(0, 50),
      dynamic=False,
      parent=self
    )
    self.box((-50,150))
    self.box((50,200))
    
  def touch_ended(self, touch):
    node_func = choice([
      self.box,
      self.ball,
    ])
    node_func(touch.location)
    
  def box(self, position):
    BoxNode(
      (randint(42, 80),randint(42, 80)),
      fill_color = (random(), random(), random()),
      position=position,
      parent=self)
    
  def ball(self, position):
    CircleNode(
      randint(25, 45),
      fill_color = (random(), random(), random()),
      position=position,
      parent=self)
    
  def update(self, ct):
    for node in self.children:
      if node.position.y < 0:
        node.parent = None
    
run(DropScene())
