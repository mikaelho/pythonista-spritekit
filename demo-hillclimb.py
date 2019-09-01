from spritekit import *
import random

class ScrollingScene(Scene):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs, physics_debug=False)
    self.step = 0
    self.step_length = 400
    self.next_step = 0
    self.block_length = 20 #steps
    self.block_width = self.step_length * self.block_length
    self.variance = 300
    self.max_variance = 500
    self.variance_increment = 25
    self.thickness = self.max_variance + 50
    self.baseline = -self.max_variance/2
    self.camera = CameraNode(parent=self)
    self.anchor_point = (0, 0.5)
    
    self.gas = False
    self.car = None
    self.current_terrain = None
    self.next_terrain = None
    self.prev_terrain = None
    self.prev_x = 0
  
    self.score = LabelNode('Score', 
      anchor_point=(1,1),
      camera_anchor=Anchor((1,1), (-20,-20)),
      alignment = LabelNode.ALIGN_RIGHT,
      vertical_alignment = LabelNode.ALIGN_TOP,
      parent=self.camera)
    
  def touch_began(self, t):
    self.gas = True
    
  def touch_ended(self, t):
    self.gas = False
    
  def update(self, ct):
    
    if self.car:
      x,y = self.car.position
      w,_ = ui.get_screen_size()
      self.camera.position = (
        x + w/2, y
      )
      if x > self.prev_x:
        score = str(int(round(x,-2))) + ' m'
        self.score.text = score
        self.prev_x = x
    
    if self.gas:
      self.car.apply_force((200,0))
      #self.car.apply_torque(.1)
      self.front_wheel.apply_torque(-.2)
      self.back_wheel.apply_torque(-.2)
    
    if (self.current_terrain is not None
      and self.next_terrain is None
      and self.camera.position.x > self.current_terrain.position.x + self.block_width/2):
      if self.variance < self.max_variance:
        self.variance += self.variance_increment
      self.next_terrain = self.generate_terrain()
      self.next_terrain.position = (
        self.current_terrain.position.x + self.block_width,
        0
      )
      if self.prev_terrain is not None:
        self.prev_terrain = None
        
    if (self.next_terrain is not None
      and self.camera.position.x > self.next_terrain.position.x):
      self.prev_terrain = self.current_terrain
      self.current_terrain = self.next_terrain
      self.next_terrain = None

  def generate_terrain(self, initial=False):
    l = self.step_length
    v = self.variance
    h = int(v/2)
    b = -v/2-1000

    if initial:
      points = [
        (0,0), (l,0), (2*l,0), (3*l, random.randint(0, h))
      ]
      start_index = 4
    else:
      start_index = 2
      points = [
        (0,0), (l, random.randint(0, h))
      ]
    for i in range(start_index, self.block_length): #20
      x = i * l
      y = random.randint(-h, h)
      points.append((x,y))
    points.append((self.block_length*l, 0))
    
    path = PathNode.quadcurve(points)
    top_surface = PathNode.quadcurve(points[1:])
    
    for point in [(self.block_length*l, b), (0,b)]:
      path.line_to(*point)
    path.close()
    
    path_node = PathNode(
      path,
      fill_color='#059d30',
      line_width=0,
      no_body=True,
      parent=self)
      
    surface_node = EdgePathNode(
      top_surface,
      parent=path_node
    )
    
    surface_node.friction = 1.0

    return path_node


scene = ScrollingScene()
terrain = scene.current_terrain = scene.generate_terrain(initial=True)
w,h = terrain.size
terrain.position = (
  0, w/2)

scene.car = SpriteNode('images/car.png',
  fill_color='white',
  position = (100,100),
  velocity=(500,0),
  density=.5,
  parent=scene)
  
scene.back_wheel = SpriteNode('images/wheel.png',
position=(-75,-35),
pinned=True,
friction=1.0,
size=Size(30,30),
parent=scene.car)

scene.front_wheel = SpriteNode('images/wheel.png',
position=(70,-33),
pinned=True,
friction=1.0,
size=Size(30,30),
parent=scene.car)

scene.camera.scale = 2

run(scene)
