from spritekit import *
from random import *

class DropScene(Scene):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.anchor_point = (0.5, 0)
    BoxNode((250,20),
      fill_color='black',
      position=(0, 50),
      dynamic=False,
      parent=self
    )
    
  def touch_ended(self, touch):
    node_func = choice([
      lambda **kw: CircleNode(
        randint(25, 45), **kw),
      lambda **kw: BoxNode(
        (randint(42, 80),randint(42, 80)),
        **kw)
    ])
    node = node_func(
      fill_color = (random(), random(), random()),
      position = touch.location,
      parent=self
    )
    
  def update(self, ct):
    for node in self.children:
      if node.position.y < 0:
        node.parent = None
    if len(self.children) == 0:
      LabelNode(text='Vicrory!',
        position=(0, 100),
        parent=self)
    
run(DropScene())
