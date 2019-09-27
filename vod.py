from spritekit import *
import vector, arrow
from vector import Vector as V
from random import *

class Buoy(CircleNode): pass

Node.collision_groups = (
  ('rock', ('rock', 'ship', 'last_buoy', 'connector')),
)
Node.contact_groups = (
  ('ship', ('rock', 'first_buoy', 'sensor_of_last_buoy')),
)
Node.field_groups = (
  ('vortex', 'ship'),
)

class RaceGame:
  
  playfield = Size(2000, 2000)
  buoy_amount = 4
  rock_amount = 10
  #rock_min = 20
  #rock_max = 40
  rock_velocity_max = 50
  rock_angular_max = 2
  
  #object_category = 1
  #ship_category = 1+2
  #object_contact = 1
  #ship_contact = 2 # Detect ship
  #buoy_collision = 0 # Not colliding
  #ship_field = 4
  
  def __init__(self, scene):
    self.scene = scene
    self.scene.game = self
    self.visited = 0
    
    pf = self.playfield
    
    self.scene.set_edge_loop(
      -pf.width/2, -pf.height/2,
      pf.width, pf.height)
    BoxNode(pf,
      no_body=True,
      alpha=0.3,
      glow_width=20,
      parent=self.scene
    )
    
    self.cells_to_a_side = math.ceil(math.sqrt(self.rock_amount*1.5+self.buoy_amount+1))
    self.cell_size = self.playfield/self.cells_to_a_side
    half_cells = math.floor(self.cells_to_a_side/2)
    self.cells = [
      (x,y) 
      for x in range(-half_cells, half_cells) 
      for y in range(-half_cells, half_cells)
    ]
    self.cells.remove((0,0))
    
    buoy_possibilities = [
      (x,y) for (x,y) in self.cells
      if V(x,y).magnitude > half_cells/4 and V(x,y).magnitude < 3*half_cells/4
    ]
    self.buoys = []
    for pos in sample(buoy_possibilities, self.buoy_amount):
      self.cells.remove(pos)
      self.place_buoy(pos)
      
    self.place_rocks()
      
    self.place_ship()
    self.place_light()
    self.add_hud_elements()
    self.update_buoys()
    
    self.ship.density = 100
    
    self.scene.initialized = True
    
    self.signal_from_here_to_there(self.ship.position, self.buoys[0].position)
    
  def add_hud_elements(self):
    self.time = LabelNode('', 
      anchor_point=(1,1),
      camera_anchor=Anchor((1,1), (-20,-50)),
      font=('Courier', 16),
      alpha=0.8,
      z_position=1,
      alignment = LabelNode.ALIGN_RIGHT,
      vertical_alignment = LabelNode.ALIGN_TOP,
      parent=self.scene.camera)
      
    b = SpriteNode(
      'spc:LaserRed6',
      #color='grey',
      #color_blend=1.0,
      anchor_point=(0.5,0),
      rotation=-math.pi/2,
      camera_anchor=Anchor((0,1), (20, -50)),
      alpha=0.9,
      no_body=True,
      parent=self.scene.camera
    )
    
    self.health = SpriteNode(
      'spc:LaserRed2',
      #color='grey',
      #color_blend=1.0,
      anchor_point=(0.5,0),
      no_body=True,
      parent=b
    )
    s = self.health.size
    s.height = 0
    self.health.size = s
      
    '''
    b = ShapeNode(ui.Path.rect(0,0,100,-5),
      hull=True,
      no_body=True,
      anchor_point=(0,1),
      camera_anchor=Anchor((0,1), (20, -50)),
      alpha=0.8,
      z_position=1,
      parent=self.scene.camera)
    self.health = ShapeNode(
      ui.Path.rect(0,0,100,-5),
      anchor_point=(0,0),
      hull=True,
      no_body=True,
      fill_color='white',
      parent=b)
    '''

    '''
    self.scene.compass = Node(
      z_position=1,
      alpha=0.5,
      parent=self.scene.ship
    )    
    CircleNode(2,
      fill_color='red',
      line_color='red',
      no_body=True,
      hidden=True,
      position=(30,0),
      parent=self.scene.compass
    )
    self.set_compass_constraint()
    '''
      
  def update_buoys(self):
    '''
    c = Constraint.orient_to_node(
      self.buoys[self.visited]
    )
    c.reference_node = self.scene.ship
    self.scene.compass.constraints = [c]
    '''
    
    A = Action
    self.buoys[self.visited].run_action(
      A.forever([
        A.scale_to(1.2, timing=A.EASE_IN_OUT),
        A.scale_to(1.0, timing=A.EASE_IN_OUT),
      ]),
      'pulse'
    )
    
  def place_ship(self):
    position = self.pos_in_cell((0,0))
    self.ship = Ship(
      name='ship',
      #category_bitmask=self.ship_category,
      #collision_bitmask=self.object_category,
      #contact_bitmask=self.object_contact,
      #field_bitmask=self.ship_field,
      position=position,
      parent=self.scene)
    self.scene.camera.add_constraint(Constraint.distance_to_node(self.ship, Range.constant(0)))
    
  def place_light(self):
    LightNode(
      category_bitmask=1,
      light_color='white',
      falloff=1.1,
      parent=self.ship,
    )
    
  def place_buoy(self, cell):   
    position = self.pos_in_cell(cell)
    names = ['first_buoy']+['buoy']*(self.buoy_amount-2)+['last_buoy']
    parent = Node(
      position=position,
      parent=self.scene)
    buoy = Buoy(20,
      name=names[len(self.buoys)],
      #category_bitmask=self.ship_contact,
      #collision_bitmask=self.buoy_collision,
      density=50,
      fill_color='black',
      line_color='red',
      font=('Courier', 24),
      alpha=0.5,
      glow_width=10,
      z_position=-1,
      dynamic=False,
      #position=position,
      parent=parent)
    self.buoys.append(buoy)
    LabelNode(text=str(len(self.buoys)),
      alpha=1.0,
      vertical_alignment=LabelNode.ALIGN_MIDDLE,
      #position=position,
      parent=parent
    )
    buoy_number = len(self.buoys)
    if buoy_number == 3:
      self.place_vortex(buoy)
    if buoy_number == 4:
      pass
      #buoy.category_bitmask = self.ship_category
      #buoy.collision_bitmask = self.object_category
      
  def place_vortex(self, buoy):
    self.vortex_buoy = buoy
    vortex = SpriteNode(
      'shp:x3',
      no_body=True,
      alpha=0.3,
      scale=10,
      z_position=-1,
      parent=buoy)
    vortex.warp = WarpGrid(21,21).set_spiral(-math.pi*2)  
    vortex.run_action(Action.forever(
      Action.rotate_by(math.pi/2)))
     
    # Vortex field does not seem to work
    # Replaced by a check in update
    vortex_field = FieldNode.vortex(
      name = 'vortex',
      parent = self.scene,
      position = buoy.position,
      region = Region.radius(300),
      strength = 1,
      falloff = 0,
      #category_bitmask = self.ship_field,
    )

  def place_rocks(self):
    rock_names = (
      'spc:MeteorGrayBig1',
      'spc:MeteorGrayBig2',
      'spc:MeteorGrayBig3',
      'spc:MeteorGrayBig4',
      'spc:MeteorGrayMed1',
      'spc:MeteorGrayMed2',
      'spc:MeteorGraySmall1',
      'spc:MeteorGraySmall2',
      #'spc:MeteorGrayTiny1',
      #'spc:MeteorGrayTiny2'
    )
    textures = [
      Texture(name) for name in rock_names
    ]
    for pos in sample(self.cells, self.rock_amount):
      self.cells.remove(pos)
      position = self.pos_in_cell(pos)
      rock = SpriteNode(choice(textures),
        name='rock',
        density=100,
        lighting_bitmask=1,
        color=(random(),)*3,
        color_blend=min(0.5,random()),
        smooth=True,
        position=position,
        velocity=(
          randint(-self.rock_velocity_max, self.rock_velocity_max), 
          randint(-self.rock_velocity_max, self.rock_velocity_max)),
        angular_velocity = randint(-self.rock_angular_max, self.rock_angular_max),
        parent=self.scene)
      #rock.warp = WarpGrid(5,5).soften()
      rock.scale = 0.75
    
  def pos_in_cell(self, cell):
    return tuple((
      cell[i] * self.cell_size[i] +
      randint(int(self.cell_size[i]/10), math.floor(self.cell_size[i]))
      for i in [0, 1]
    ))
    
  def signal_from_here_to_there(self, start, end):
    signal = CircleNode(20,
      no_body=True,
      #category_bitmask=self.ship_contact,
      #collision_bitmask=self.buoy_collision,
      line_color='red',
      glow_width=10,
      z_position=-1,
      position=start,
      alpha=0.0,
      parent=self.scene)
    A = Action
    signal.run_action([
      A.alpha_to(0.5, duration=0.3),
      A.scale_to(0.1, duration=0.3),
      A.move_to(end),
      A.scale_to(1.0, duration=0.3),
      A.fade_out()
    ])
    
  def process_contacts(self, data):
    if not self.scene.initialized: return 
    a = data.node_a
    b = data.node_b
    #print(a.name, b.name)

    if type(a) == Buoy or type(b) == Buoy:
      buoy_hit = self.buoys[self.visited]
      active_category = buoy_hit.category_bitmask
      buoy_hit.category_bitmask = 0
      buoy_hit.line_color = 'green'
      buoy_hit.stop_actions()
      
      self.visited += 1
      
      if self.visited < self.buoy_amount: 
        self.buoys[self.visited].category_bitmask = active_category
        self.signal_from_here_to_there(
          self.buoys[self.visited-1].position,
          self.buoys[self.visited].position)
        
        if self.visited == self.buoy_amount - 1:
          self.sensor = CircleNode(50,
            name='sensor_of_last_buoy',
            hidden=True,
            dynamic=False,
            position=self.buoys[self.visited].position,
            parent=self.scene
          )
        self.update_buoys()
      else:
        l = ui.Label(text=self.time.text,
          text_color='white',
          font=('Courier', 32),
          alignment=ui.ALIGN_CENTER,
          flex='LRTB',
        )
        l.size_to_fit()
        l.center=self.scene.view.bounds.center()
        self.scene.view.add_subview(l)
        self.scene.run_action(Action.fade_out(duration=2))
        
    elif a.name == 'sensor_of_last_buoy' or b.name == 'sensor_of_last_buoy':
      last_buoy = self.buoys[-1]
      delta = Vector(last_buoy.position-self.ship.position)
      p = ui.Path()
      p.line_to(*delta)
      connector = ShapeNode(p,
        name='connector',
        line_color='white',
        #line_width=5,
        position=self.ship.position,
        z_position=min(self.ship.z_position - 1, last_buoy.z_position - 1)-1,
        parent=self.scene)
      Joint.pin(self.ship, connector, self.ship.position)

      Joint.pin(last_buoy.parent, connector, last_buoy.position)
      last_buoy.parent.dynamic = True
      
      self.sensor.parent = None
    else:
      print('d')
      self.ship.damage += data.impulse/10
      damage_factor = min(1.0, 
        self.ship.damage/
        self.ship.max_damage)
      '''
      self.health.path = ui.Path.rect(
        0,0,percentage_left,-5)
      '''
      
      self.health.run_action(
        Action.height_to(damage_factor*self.health.parent.size.height)
      )
      
      if self.ship.damage > self.ship.max_damage:
        self.scene.run_action(Action.fade_out(duration=2))
    
    
class RaceScene(Scene):
  
  def __init__(self, **kwargs):
    self.initialized = False
    super().__init__(can_pan=False, can_pinch=True, **kwargs)
    self.background_color = 'black'
    self.touch_thrust = []
    self.touch_rotate = []
    self.touch_thrust_start = 0
    self.touch_rotate_start = 0
    self.multitouch_enabled = True
    self.anchor_point = (0.5,0.5)
    self.camera = CameraNode(parent=self)

    self.camera.layers.append(Layer(
      Texture('images/spacetile_transparent.PNG'), pan_factor=0.2, alpha=0.4))
    #self.camera.layers.append(Layer(
    #  Texture('images/spacetile_bottom.jpg'),
    #  pan_factor=0))
    
  def touch_began(self, t):
    if t.location.x > self.camera.position.x:
      self.touch_thrust.append(t.touch_id)
      if len(self.touch_thrust) == 1:
        self.touch_thrust_start = self.convert_to_view(t.location).y
    else:
      self.touch_rotate.append(t.touch_id)
      if len(self.touch_rotate) == 1:
        self.touch_rotate_start = t.location.x
        
  def touch_moved(self, t):
    if len(self.touch_rotate) == 1 and t.touch_id == self.touch_rotate[0]:
      self.game.ship.angular_velocity = 0
      '''
      delta = Vector(t.location - t.prev_location)
      #heading_tangent =
      heading_tangent = Vector(1,0)
      heading_tangent.radians = self.ship.rotation+math.pi/2
      rotate = delta.dot_product(heading_tangent)
      self.ship.rotation += rotate/75
      '''
      self.game.ship.rotation += (t.location.x - t.prev_location.x)/50
    if len(self.touch_thrust) == 1 and t.touch_id == self.touch_thrust[0]:
      delta = self.touch_thrust_start - self.convert_to_view(t.location).y
      self.game.ship.thrust = max(0, min(100, delta))
    
  def touch_ended(self, t):
    if t.touch_id in self.touch_thrust:
      self.touch_thrust.remove(t.touch_id)
      if len(self.touch_thrust) == 0:
        self.game.ship.thrust = 0
    if t.touch_id in self.touch_rotate:
      self.touch_rotate.remove(t.touch_id)
    
  def update(self, ct):
    if not self.initialized:
      self.start_time = ct
      return
    
    if self.game.visited < self.game.buoy_amount: 
      elapsed = arrow.get(ct - self.start_time)
      self.game.time.text = elapsed.format('m:ss:SS')
    
    self.game.ship.trigger_thrust()
    
    #self.game.simulate_vortex()

    #lead = vector.Vector(self.ship.velocity)
    #lead.magnitude = min(lead.magnitude, 100)
    #self.camera_spot.run_action(
    #  Action.move_to(tuple(lead), duration=2.0), 'lead'
    #)
    #self.last_thrust = ct
    
    self.camera.update_layers()
    
  def contact(self, data):
    if not self.initialized: return
    self.game.process_contacts(data)
    
    
class Ship(ShapeNode):
  
  def __init__(self, **kwargs):
    self.thrust = 0
    self.max_thrust = 500
    self.damage = 0
    self.max_damage = 100
    
    p = ui.Path()
    p.line_to(-25,10)
    p.line_to(-25,-10)
    p.close()
    #super().__init__('spc:PlayerShip1Orange',**kwargs)
    super().__init__(p,
      line_color='white',
      fill_color='black',
      **kwargs,
      )
    self.thrust_texture = Texture('shp:Explosion03')

  def trigger_thrust(self):
    
    if self.thrust == 0: return 

    thrust = vector.Vector(
      self.max_thrust/100*self.thrust, 0
    )
    thrust.radians = self.rotation
    self.apply_force(tuple(thrust))

    emission_angle = self.rotation - math.pi
    particle_life = self.thrust * 0.001
    
    EmitterNode(parent=self,
      target_node=self.parent,
      particle_birth_rate = 10,
      num_particles_to_emit = 2,
      particle_life_time = particle_life,
      particle_size = Size(10,10),
      particle_alpha = 0.5,
      particle_alpha_range = 0.1,
      particle_alpha_speed = -1.0,
      emission_angle = emission_angle,
      emission_angle_range = 0.2,
      emission_distance = 50,
      particle_speed = 1000,
      particle_color = 'white',
      
      #particle_texture = self.thrust_texture.texture
    )
    
scene = RaceScene(
  physics=SpacePhysics,
  #physics_debug=True,
  #field_debug=True,
)

game = RaceGame(scene)
      
run(scene, 'full_screen', hide_title_bar=True)

scene.camera.scale = 1.5
