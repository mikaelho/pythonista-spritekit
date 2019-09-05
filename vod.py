from spritekit import *
import vector

class RaceScene(Scene):
  
  def __init__(self, **kwargs):
    self.initialized = False
    super().__init__(**kwargs)
    self.background_color = 'black'
    self.touch_thrust = []
    self.touch_rotate = []
    self.touch_rotate_start = 0
    self.multitouch_enabled = True
    self.anchor_point = (0.5,0.5)
    self.camera = CameraNode(parent=self)
    self.prev_camera_pos = self.camera.position
    self.scaffold = Node(parent=self)
    self.ship = Ship(
      rotation=math.pi/4, 
      parent=self)
    self.camera_spot = Node(parent=self.scaffold)
    #self.bg_tile = Texture('images/spacetile_transparent.PNG')
    self.bg = Background(
      parent=self.camera)
    self.bg.layers.append(BackgroundLayer(
      Texture('images/spacetile_transparent.PNG'), pan_factor=0.9))
    self.bg.layers.append(BackgroundLayer(
      Texture('images/spacetile_bottom.jpg'),
      pan_factor=0.3))
    self.scaffold.add_constraint(Constraint.distance_to_node(self.ship, Range.constant(0)))
    self.camera.add_constraint(Constraint.distance_to_node(self.camera_spot, Range.limits(-25, 25)))
    self.initialized = True
    
  def touch_began(self, t):
    if t.location.x > self.camera.position.x:
      self.touch_thrust.append(t.touch_id)
    else:
      self.touch_rotate.append(t.touch_id)
      if len(self.touch_rotate) == 1:
        self.touch_rotate_start = t.location.x
        
  def touch_moved(self, t):
    if len(self.touch_rotate) == 1 and t.touch_id == self.touch_rotate[0]:
      self.ship.rotation += (t.location.x - t.prev_location.x)/50
    
  def touch_ended(self, t):
    if t.touch_id in self.touch_thrust:
      self.touch_thrust.remove(t.touch_id)
    if t.touch_id in self.touch_rotate:
      self.touch_rotate.remove(t.touch_id)
    
  def update(self, ct):
    if not self.initialized: return
    
    if len(self.touch_thrust) > 0:
      self.ship.trigger_thrust(self.ship.rotation, self.ship.velocity)

      thrust = vector.Vector(
        self.ship.thrust, 0
      )
      thrust.radians = self.ship.rotation
      self.ship.apply_force((thrust.x, thrust.y))
      lead = vector.Vector(self.ship.velocity)
      lead.magnitude = min(lead.magnitude, 100)
      self.camera_spot.position = tuple(lead)
      self.last_thrust = ct
    
    delta_pos = self.camera.position - self.prev_camera_pos
    self.prev_camera_pos = self.camera.position
    if abs(delta_pos) > 0:
      self.bg.delta_pan(delta_pos)
    
    
class Ship(ShapeNode):
  
  def __init__(self, **kwargs):
    self.thrust = 5
    
    p = ui.Path()
    p.line_to(-50,20)
    p.line_to(-50,-20)
    p.close()
    #super().__init__('spc:PlayerShip1Orange',**kwargs)
    super().__init__(p,
      line_color='white',
      fill_color='black',
      **kwargs,
      )
    self.thrust_texture = Texture('shp:Explosion03')

  def trigger_thrust(self, heading, velocity):
    #return
    EmitterNode(parent=self,
      target_node=self.parent,
      particle_birth_rate = 10,
      num_particles_to_emit = 2,
      particle_life_time = 0.1,
      particle_size = Size(10,10),
      particle_alpha = 0.9,
      particle_alpha_range = 0.1,
      particle_alpha_speed = -1.0,
      emission_angle = heading - math.pi,
      emission_angle_range = 0.2,
      emission_distance = 50,
      particle_speed = 1000,
      
      particle_texture = self.thrust_texture.texture)
    
      
run(RaceScene(physics=SpacePhysics, physics_debug=True))
