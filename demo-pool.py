from spritekit import *
import ui, math, random
import vector

scene = Scene(
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
  
ball_radius = 9
  
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
  radius=ball_radius,
  fill_color=player1,
  line_color=get_highlight_color(player1),
  parent=scene,
  position=tuple(ball_pos),
)
  
balls = [
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
]
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
    parent=scene,
    position=(x,y),
  )

run(scene)

class CueBall(CircleNode):
  
  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.touch_enabled = True
  
  def touch_ended(self, touch):
    touch_pos = self.convert_point_to(touch.location, self.scene)
    t = self.position - touch_pos
    self.velocity = (2*t.x, 2*t.y)
    
cue_ball = CueBall(
  radius=ball_radius,
  fill_color='white',
  parent=scene,
  position=(0, -125),
  #velocity=(random.randint(-10,10), 400),
)
  
#print(dir(cue_ball.node.physicsBody()))

