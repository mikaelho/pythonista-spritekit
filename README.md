# iOS SpriteKit wrapper for Pythonista

If you are familiar with Pythonista scene module, many things will feel familiar. Look at Apple SpriteKit docs for more details.

## About nodes in general

By default, it is assumed that you want your nodes to have an underlying body for physics simulations - if not, you would using the scene module. Thus all visible bodies have a physics body created automatically. If you do not want this to happen, provide the no_body=True parameter at creation, or set node.body=None at a later time.

## Supported nodes and attributes

* Node
	* Scene

Visible:
	* ShapeNode
		* BoxNode
		* CircleNode
	* SpriteNode
	* LabelNode
	
Special:
	* CameraNode
	* FieldNode
	* EmitterNode

Obsolete:
* PathNode
* PointsNode


### Node

All other nodes are inherited from Node and share its attributes. All writeable attributes can also be provided at initialization.

* children
* parent
* scale
* scale_x
* scale_y
* affected_by_gravity - boolean
* allows_rotation - boolean
* alpha
* anchor_point - default (0.5, 0.5)
* area - read only
* angular_damping - 0.0 to 1.0
* angular_velocity
* background_color = fill_color
* bbox - with children
* bullet_physics - boolean
* contact_bitmask
* density
* dynamic - boolean
* fill_color = background_color
* frame - this node only
* friction - 0.0 to 1.0
* hidden
* linear_damping - 0.0 to 1.0
* mass
* name
* physics_body - ObjC object
* position
* resting - boolean
* restitution - 0.0 to 1.0
* rotation
* size
* touch_enabled
* velocity
* z_position

### ShapeNode(path)

Argument: ui.Path or a list of points

By default creates a shape node with a texture-based body (pixel-level collisions, poorer performance).

Optional:
* smooth=True to create a smooth spline shape from the given path or points
* hull=True to create a physics body based on an approximated outer hull surrounding the given points (less accurate, more performant)

Has these attributes:

* antialiased
* fill_color (from Node)
* fill_texture
* glow_width
* line_color
* line_width
* path - update the path (and body)

### PointsNode(points, smooth=False)

Arguments: list of points, if smooth is true, the line connecting the points will be a smooth spline

### BoxNode(size) - inherits from PathNode

### CircleNode(radius) - inherits from PathNode

### SpriteNode(image)

### FieldNode

Use the following class methods to create field nodes:

* drag
* electric
* linear_gravity
* magnetic
* noise
* radial_gravity
* spring
* turbulence
* velocity_texture
* velocity_vector
* vortex

FieldNodes have the following attributes:

* enabled - default True
* exclusive - default False
* falloff
* strength
* region - see Region in supporting classes

### LabelNode(text)

Does not have a physics body. If you need a body, create as a child of a BoxNode.

Attributes:

* text
* font = (font_name, font_size)
* font_color
* font_name
* font_size
* alignment - LabelNode.ALIGN_CENTER/ALIGN_LEFT/ALIGN_RIGHT
* vertical_alignment - LabelNode.ALIGN_BASELINE/ALIGN_MIDDLE/ALIGN_TOP/ALIGN_BOTTOM

### CameraNode

## Supporting classes

* Texture
* Region
* Constraint
* Range

### Texture

Initializer accepts image name, image path, ui.Image, Texture or SKTexture.

Methods:

* crop(rect) - rectangle in unit space (0.0-1.0). Texture is not copied.

### Region

Create a region to constrain a field effect with one of the following class methods:

* Creating a region
	* infinite
	* size - centered on the origin
	* radius
	* path
* With another region
	* inverse
	* difference
	* intersection
	* union

Regions have the following attributes:

* path
* contains(point)

### Constraint



### Range


