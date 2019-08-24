from spritekit import *
import ui, math, random
import vector

ball_radius = 9
pocket_radius = 12

pocketed = []
to_remove = []

class PoolScene(Scene):
  
  def contact(self, a, b):
    global to_remove
    ball = a if b.name == 'sensor' else b
    to_remove.append(ball)
    
  def update(self):
    global pocketed, to_remove
    
    for ball in to_remove:
      if type(ball) == CueBall:
        ball.position = (0, -290)
        ball.velocity = (0,0)
        ball.category_bitmask = 2
        ball.collision_bitmask = 2
      else:
        ball.position = (
          -141 + len(pocketed) * (2 * ball_radius + 5),
          290
        )
        ball.velocity = (0,0)
        pocketed.append(ball)
      
    to_remove.clear()
        

scene = PoolScene(
  background_color='green',
  physics=BilliardsPhysics,
  anchor_point=(0.5,0.5),
  #physics_debug=True,
)

table_texture = Texture('images/pool_table.PNG')

left_half = table_texture.crop((
  0.0, 0.0, 0.5, 1.0))
right_half = table_texture.crop((
  0.5, 0.0, 0.5, 1.0))

table_left = SpriteNode(left_half,
  dynamic=False,
  allows_rotation=False,
  parent=scene)

table_left.position = (-75,0)
table_right = SpriteNode(right_half,
  dynamic=False,
  allows_rotation=False,
  parent=scene)
table_right.position = (75,0)

v = 240
h = 130
h_shift = 5

pockets = (
  (-h, -3),
  (-h+h_shift, v),
  (-h+1.5*h_shift, -v),
  (h, -3),
  (h-h_shift, v),
  (h-1.5*h_shift, -v),
)

for pos in pockets:
  pocket = CircleNode(
    radius=pocket_radius,
    fill_color='black',
    line_color=(0,0,0,0.5),
    dynamic=False,
    line_width=5,
    parent=scene,
    position=pos,
  )
  pocket.body = None
  
  f = FieldNode.radial_gravity()
  f.parent = scene
  f.position = pos
  f.falloff = 2
  f.region = Region.radius(pocket_radius+4)
  
  pocket_sensor = CircleNode(1,
    name='sensor',
    contact_bitmask=1,
    dynamic=False,
    alpha=0,
    parent=scene,
    position=pos)
  
ball_pos = vector.Vector(0, 110)
player1 = 'blue'
player2 = 'red'

def get_highlight_color(color):
  c = list(ui.parse_color(color))
  for i in range(3):
    v = c[i]
    c[i] = min(1.0, v + .5)
  return tuple(c)
  
CircleNode(
  name='ball',
  radius=ball_radius,
  fill_color=player1,
  line_color=get_highlight_color(player1),
  category_bitmask=1,
  collision_bitmask=1,
  parent=scene,
  position=tuple(ball_pos),
)
  
balls = (
  (60, player2),
  (180, player1),
  (120, player2),
  (0, 'black'),
  (0, player1),
  (60, player2),
  (180, player1),
  (180, player2),
  (180, player1),
  (120, player2),
  (0, player1),
  (0, player2),
  (0, player2),
  (0, player1),
)
vector
to_next_ball = vector.Vector(2*ball_radius,0)
for angle, color in balls:
  to_next_ball.degrees = angle
  ball_pos += to_next_ball
  x,y = ball_pos
  
  CircleNode(
    radius=ball_radius,
    fill_color=color,
    line_color=get_highlight_color(color),
    category_bitmask=1,
    collision_bitmask=1,
    parent=scene,
    position=(x,y),
  )

run(scene)

class CueBall(CircleNode):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.touch_enabled = True
    
  def touch_moved(self, touch):
    if self.collision_bitmask == 1:
      return
    self.position = self.convert_point_to(touch.location, self.scene)
  
  def touch_ended(self, touch):
    touch_pos = self.convert_point_to(touch.location, self.scene)
    if self.collision_bitmask == 1:
      t = self.position - touch_pos
      self.velocity = (3*t.x, 3*t.y)
    else:
      play_area = Rect(-118, -228, 236, 456)
      if play_area.contains_point(touch_pos):
        self.collision_bitmask = 1
        self.category_bitmask = 1
      else:
        self.position = (0, -290)
        
        
    
cue_ball = CueBall(
  radius=ball_radius,
  fill_color='white',
  parent=scene,
  category_bitmask=1,
  collision_bitmask=1,
  position=(0, -125),
  #velocity=(random.randint(-10,10), 400),
)
  
#print(dir(cue_ball.node.physicsBody()))

