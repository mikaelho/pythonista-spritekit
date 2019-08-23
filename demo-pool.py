from spritekit import *
import ui, math, random

scene = Scene(
  background_color='green',
  physics=BilliardsPhysics,
  anchor_point=(0.5,0.5),
  physics_debug=True,
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
w,h = table_left.size
print(w,h)
table_left.position = (w,0)
table_right = SpriteNode(right_half,
  dynamic=False,
  allows_rotation=False,
  parent=scene)
table_left.position = (-w,0)
  
CircleNode(
  radius=25,
  fill_color='white',

  velocity=(
    random.randint(-100,100),
    random.randint(-100,100),
  ),
  parent=scene)
  
scene.camera = CameraNode(
  #scale=1.5,
  rotation=math.pi/2,
  parent=scene
)

run(scene)
