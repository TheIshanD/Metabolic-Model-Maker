"""Takes in a KGML file and creates an interactive visual representation of it"""
import xml.etree.ElementTree as ET
import pygame
from networking import NeuralNetwork, Neuron


def parse_kgml(file_path):
    """Takes in a KGML file, returns a neural network

    Args:
        file_path (str): the filepath
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    neural_net = NeuralNetwork()

    # Iterate over all non-group entries of KGML
    for entry in root.iter("entry"):
        if entry.attrib["type"] == "group":
            continue

        id_ = entry.attrib["id"]
        name = entry.attrib["name"].split(",")[0].split(".")[0]
        type_ = entry.attrib["type"]

        # Ignore irrelevant entries
        if type_ == "map":
            continue

        # Input the coordinates of the Entry (correlates with KGML file)
        pos = (0, 0)
        graphics_name = "n/a"
        for graphics in entry.iter("graphics"):
            if "name" in graphics.attrib:
                graphics_name = graphics.attrib["name"].split(",")[0].split(".")[0]
            pos = (int(graphics.attrib["x"]), int(graphics.attrib["y"]))

        # Create a neuron to represent the Entry
        neuron = Neuron(id_, name, type_, pos, graphics_name)
        neural_net.neurons[id_] = neuron

    # Iterate over all groups in KGML
    counter = 0
    for group in root.iter("entry"):
        if group.attrib["type"] != "group":
            continue

        # Input the coordinates of the Entry (correlates with KGML file)
        pos = (0, 0)
        for graphics in group.iter("graphics"):
            pos = (int(graphics.attrib["x"]), int(graphics.attrib["y"]))

        # Create a neuron to represent the group
        counter += 1
        group_neuron = Neuron(group.attrib["id"],
                              group.attrib["name"] + str(counter),
                              "group",
                              pos,
                              "Group" + str(counter))
        neural_net.neurons[group.attrib["id"]] = group_neuron

        # Connect the components of the group to the group
        num_comps = 0
        for _ in group.iter("component"):
            num_comps += 1

        for component in group.iter("component"):
            component_id = component.attrib["id"]
            component_neuron = neural_net.neurons[component_id]

            component_neuron.connect(group_neuron, 1/num_comps)

    # Iterate over all the relations in the KGML
    for relation in root.iter("relation"):
        # Determine the two entries that are being interacted with
        source_id = relation.attrib["entry1"]
        target_id = relation.attrib["entry2"]
        source_neuron = neural_net.neurons[source_id]
        target_neuron = neural_net.neurons[target_id]

        # Iterate over all the subtypes. (THIS CAN/SHOULD BE UPDATED AS WE GAIN MORE KNOWLEDGE OF EFFECTS)
        count = 0
        for subtype in relation.iter("subtype"):
            count += 1

            if count == 2:
                break
            type_ = subtype.attrib["name"]

            if type_ in ["activation", "expression", "binding/association", "indirect effect", "missing interaction",
                         "phosphorylation"]:
                # Define positive relations
                source_neuron.connect(target_neuron, 1)
            elif type_ in ["inhibition", "repression", "dissociation", "methylation", "dephosphorylation"]:
                # Define negative relations
                source_neuron.connect(target_neuron, -1)
            else:
                # All other types of relationships
                pass

    return neural_net


# Credit to u/plastic_astronomer for draw_arrow function
def draw_arrow(
        surface: pygame.Surface,
        start: pygame.Vector2,
        end: pygame.Vector2,
        color: pygame.Color,
        body_width: int = 2,
        head_width: int = 4,
        head_height: int = 2,
):
    """Draw an arrow between start and end with the arrow head at the end.

    Args:
        surface (pygame.Surface): The surface to draw on
        start (pygame.Vector2): Start position
        end (pygame.Vector2): End position
        color (pygame.Color): Color of the arrow
        body_width (int, optional): Defaults to 2.
        head_width (int, optional): Defaults to 4.
        head_height (float, optional): Defaults to 2.
    """
    arrow = start - end
    angle = arrow.angle_to(pygame.Vector2(0, -1))
    body_length = arrow.length() - head_height

    # Create the triangle head around the origin
    head_vertices = [
        pygame.Vector2(0, head_height / 2),  # Center
        pygame.Vector2(head_width / 2, -head_height / 2),  # Bottomright
        pygame.Vector2(-head_width / 2, -head_height / 2),  # Bottomleft
    ]
    # Rotate and translate the head into place
    translation = pygame.Vector2(0, arrow.length() - (head_height / 2)).rotate(-angle)
    for vertices in head_vertices:
        vertices.rotate_ip(-angle)
        vertices += translation
        vertices += start

    pygame.draw.polygon(surface, color, head_vertices)

    # Stop weird shapes when the arrow is shorter than arrow head
    if arrow.length() >= head_height:
        # Calculate the body rect, rotate and translate into place
        body_vertices = [
            pygame.Vector2(-body_width / 2, body_length / 2),  # Topleft
            pygame.Vector2(body_width / 2, body_length / 2),  # Topright
            pygame.Vector2(body_width / 2, -body_length / 2),  # Bottomright
            pygame.Vector2(-body_width / 2, -body_length / 2),  # Bottomleft
        ]
        translation = pygame.Vector2(0, body_length / 2).rotate(-angle)
        for vertices in body_vertices:
            vertices.rotate_ip(-angle)
            vertices += translation
            vertices += start

        pygame.draw.polygon(surface, color, body_vertices)


def visualize_network(network, model_path):
    """Takes in a Neural Network and generates an interactive, visual Neural Network

    Args:
        network (NeuralNetwork): A Neural Network that will be to represent the KGML file
        model_path (str): A string that is the file path to a txt model file
    """
    pygame.init()

    # Define program constants
    graph_scale = 2 / 3
    right_shift = 200
    offset_increment = 110
    num_decimals = 5
    pygame.display.set_caption("KGML Model Creator")
    font = pygame.font.Font("Tinos-Bold.ttf", 18)
    screen = pygame.display.set_mode((1000 + right_shift, 700),
                                     pygame.RESIZABLE)
    edit = font.render("Edit",
                       False,
                       pygame.Color("purple"))

    # Define state variables
    network.setup(model_path)
    neurons = network.neurons.values()
    is_viewing = False
    is_typing = False
    clicked_neuron = None
    typing_object = None
    typing_item = None
    typing_string = ""
    typing_ind = -1
    running = True

    # Start the game loop
    while running:
        # Reset Screen
        offset = 75

        screen.fill((255, 255, 255))
        _, screen_height = pygame.display.get_surface().get_size()
        pygame.draw.rect(screen,
                         pygame.Color("grey"),
                         pygame.Rect(0, 0, right_shift, screen_height))

        # Test for Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # If the tab is quit, exit the loop
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Propagate the network when space-bar is pressed
                    network.propagate_net()
                elif event.key == pygame.K_RETURN:
                    if is_typing:
                        # Change network values to typed strings
                        try:
                            if typing_item in ("value", "inc_value"):
                                # Change neuron values
                                if float(typing_string) > 1:
                                    # Set the value to one as value cannot exceed 1
                                    typing_object.value = 1.0

                                    # Set all other instances of item to value
                                    for neuron in network.neurons.values():
                                        if neuron.code == typing_object.code:
                                            neuron.value = 1.0
                                else:
                                    typing_object.value = float(typing_string)

                                    # Set all other instances of item to value
                                    for neuron in network.neurons.values():
                                        if neuron.code == typing_object.code:
                                            neuron.value = float(typing_string)
                            elif typing_item == "weight":
                                typing_object.weight = float(typing_string)

                                # Set all other instances of item to value
                                for neuron in network.neurons.values():
                                    for conn_ind, conn in enumerate(neuron.incoming_connections):
                                        if (conn.source.code == typing_object.source.code
                                                and neuron.code == typing_object.target.code):
                                            conn.weight = float(typing_string)
                            elif typing_item == "bias":
                                typing_object.bias = float(typing_string)

                                # Set all other instances of item to value
                                for neuron in network.neurons.values():
                                    if neuron.code == typing_object.code:
                                        neuron.bias = float(typing_string)
                            elif typing_item == "decay":
                                if float(typing_string) == 0:
                                    typing_string = "0.0000001"
                                typing_object.decay = float(typing_string)

                                # Set all other instances of item to value
                                for neuron in network.neurons.values():
                                    if neuron.code == typing_object.code:
                                        neuron.decay = float(typing_string)
                        except ValueError:
                            pass

                        # Reset typing state
                        typing_string = ""
                        is_typing = False
                        typing_item = None
                        typing_object = None

                elif event.key == pygame.K_BACKSPACE:
                    # Delete last typing string character
                    if is_typing:
                        if len(typing_string) > 0:
                            typing_string = typing_string[:-1]
                else:
                    # Add character to the typing string
                    if is_typing:
                        typing_string += event.unicode

            elif event.type == pygame.MOUSEBUTTONUP:
                m_x, m_y = pygame.mouse.get_pos()

                # If you are viewing a neuron panel...
                if is_viewing:

                    if 115 <= m_x <= 115 + 40 and 50 <= m_y <= 50 + 20:
                        # If current neuron value is clicked, turn on typing for value
                        is_typing = True
                        typing_item = "value"
                        typing_object = clicked_neuron
                        typing_string = ""
                        typing_ind = -1

                    if 115 <= m_x <= 115 + 40 and 75 <= m_y <= 75 + 20:
                        # If current neuron bias is clicked, turn on typing for bias
                        is_typing = True
                        typing_item = "bias"
                        typing_object = clicked_neuron
                        typing_string = ""
                        typing_ind = -1

                    if 115 <= m_x <= 115 + 40 and 100 <= m_y <= 100 + 20:
                        # If current neuron decay is clicked, turn on typing for decay
                        is_typing = True
                        typing_item = "decay"
                        typing_object = clicked_neuron
                        typing_string = ""
                        typing_ind = -1

                    # Check if the user wants to change any of the incoming connections
                    offset_copy = offset
                    for conn_ind, conn in enumerate(clicked_neuron.incoming_connections):
                        offset_copy += offset_increment

                        # If incoming connection value is clicked
                        if (135 <= m_x <= 135 + 40
                                and 50 + offset_copy <= m_y <= 50 + offset_copy + 20):
                            # Start incoming value typing state
                            is_typing = True
                            typing_item = "inc_value"
                            typing_object = conn.source
                            typing_string = ""
                            typing_ind = conn_ind

                        # If incoming connection weight is clicked
                        if (135 <= m_x <= 135 + 40
                                and 75 + offset_copy <= m_y <= 75 + offset_copy + 20):
                            # Start weight typing state
                            is_typing = True
                            typing_item = "weight"
                            typing_object = conn
                            typing_string = ""
                            typing_ind = conn_ind

                # Check if the user clicked a neuron
                for neuron in neurons:
                    n_x, n_y = neuron.pos
                    if (graph_scale * n_x - 6 + right_shift <= m_x <= graph_scale * n_x + 6 + right_shift
                            and graph_scale * n_y - 6 <= m_y <= graph_scale * n_y + 6):
                        # Set state as viewing that neuron in the panel
                        is_viewing = True
                        clicked_neuron = neuron

                        is_typing = False
                        typing_item = None
                        typing_object = None
                        typing_string = ""

        # Manage all neuron panel interactions
        if is_viewing:
            # Update panel specifically if the user is currently editing a value
            if is_typing:
                # Render neuron code and type
                text_surface = font.render(clicked_neuron.code,
                                           False,
                                           (75, 75, 0))
                type_surface = font.render("T: " + str(clicked_neuron.type),
                                           False,
                                           (75, 75, 0))

                if typing_item == "value":
                    # If currently editing current neuron value, render value with currently typed string
                    value_surface = font.render("V: " + typing_string,
                                                False,
                                                (75, 75, 0))
                    bias_surface = font.render("B: " + str(round(clicked_neuron.bias, num_decimals)),
                                               False,
                                               (75, 75, 0))
                    decay_surface = font.render("D: " + str(round(clicked_neuron.decay, num_decimals)),
                                               False, (75, 75, 0))
                elif typing_item == "bias":
                    # If currently editing bias, render bias with currently typed string
                    value_surface = font.render("V: " + str(round(clicked_neuron.value, num_decimals)),
                                                False,
                                                (75, 75, 0))
                    bias_surface = font.render("B: " + typing_string,
                                               False,
                                               (75, 75, 0))
                    decay_surface = font.render("D: " + str(round(clicked_neuron.decay, num_decimals)),
                                               False, (75, 75, 0))
                elif typing_item == "decay":
                    # If currently editing decay, render decay with currently typed string
                    value_surface = font.render("V: " + str(round(clicked_neuron.value, num_decimals)),
                                                False,
                                                (75, 75, 0))
                    bias_surface = font.render("B: " + str(round(clicked_neuron.bias, num_decimals)),
                                               False,
                                               (75, 75, 0))
                    decay_surface = font.render("D: " + typing_string,
                                               False, (75, 75, 0))
                else:
                    # If currently editing neither, render normally
                    value_surface = font.render("V: " + str(round(clicked_neuron.value, num_decimals)),
                                                False, (75, 75, 0))
                    bias_surface = font.render("B: " + str(round(clicked_neuron.bias, num_decimals)),
                                               False, (75, 75, 0))
                    decay_surface = font.render("D: " + str(round(clicked_neuron.decay, num_decimals)),
                                                False, (75, 75, 0))

                activation_surface = font.render("A: " + str(clicked_neuron.activation_type),
                                                 False,
                                                 (75, 75, 0))
            else:
                # If the user is not typing, render everything normally
                text_surface = font.render(clicked_neuron.code,
                                           False,
                                           (75, 75, 0))
                type_surface = font.render("T: " + str(clicked_neuron.type),
                                           False,
                                           (75, 75, 0))
                value_surface = font.render("V: " + str(round(clicked_neuron.value, num_decimals)),
                                            False,
                                            (75, 75, 0))
                bias_surface = font.render("B: " + str(round(clicked_neuron.bias, num_decimals)),
                                           False,
                                           (75, 75, 0))
                decay_surface = font.render("D: " + str(round(clicked_neuron.decay, num_decimals)),
                                           False,
                                           (75, 75, 0))
                activation_surface = font.render("A: " + str(clicked_neuron.activation_type),
                                                 False,
                                                 (75, 75, 0))
            # Always render neuron code, type, and value
            screen.blit(text_surface,
                        (0, 0))
            screen.blit(type_surface,
                        (0, 25))
            screen.blit(value_surface,
                        (0, 50))
            screen.blit(edit,
                        (115, 50))

            # If the neuron has at least one incoming connection, render bias and activation and editing
            if not clicked_neuron.is_input:
                screen.blit(bias_surface,
                            (0, 75))
                screen.blit(decay_surface,
                            (0, 100))
                screen.blit(activation_surface,
                            (0, 125))

                # Render a bias edit button
                screen.blit(edit,
                            (115, 75))

                screen.blit(edit,
                            (115, 100))

            # For each incoming connection, render panel components
            for conn_ind, conn in enumerate(clicked_neuron.incoming_connections):
                offset += offset_increment

                # If you are editing a value on the current connection, render it so that the user can type cleanly
                if is_typing and conn_ind == typing_ind:
                    # Always render the neuron code and the type
                    inc_text_surface = font.render(conn.source.code,
                                                   False,
                                                   (0, 0, 0))
                    inc_type_surface = font.render("T: " + str(conn.source.type),
                                                   False,
                                                   (0, 0, 0))

                    if typing_item == "inc_value":
                        # If currently editing current connection value, render value with currently typed string
                        inc_value_surface = font.render("V: " + typing_string,
                                                        False,
                                                        (0, 0, 0))
                        inc_weight_surface = font.render("W: " + str(round(conn.weight, num_decimals)),
                                                         False,
                                                         (0, 0, 0))
                    elif typing_item == "weight":
                        # If currently editing current connection weight, render weight with currently typed string
                        inc_value_surface = font.render("V: " + str(round(conn.source.value, num_decimals)),
                                                        False,
                                                        (0, 0, 0))
                        inc_weight_surface = font.render("W: " + typing_string,
                                                         False,
                                                         (0, 0, 0))
                    else:
                        # If currently editing neither, render normally
                        inc_value_surface = font.render("V: " + str(round(conn.source.value, num_decimals)),
                                                        False,
                                                        (0, 0, 0))
                        inc_weight_surface = font.render("W: " + str(round(conn.weight, num_decimals)),
                                                         False,
                                                         (0, 0, 0))
                else:
                    # If the user is not typing, render everything normally
                    inc_text_surface = font.render(conn.source.code,
                                                   False,
                                                   (0, 0, 0))
                    inc_type_surface = font.render("T: " + str(conn.source.type),
                                                   False,
                                                   (0, 0, 0))
                    inc_value_surface = font.render("V: " + str(round(conn.source.value, num_decimals)),
                                                    False,
                                                    (0, 0, 0))
                    inc_weight_surface = font.render("W: " + str(round(conn.weight, num_decimals)),
                                                     False,
                                                     (0, 0, 0))
                # Actually render each incoming connection
                screen.blit(inc_text_surface,
                            (20, offset))
                screen.blit(inc_type_surface,
                            (20, offset + 25))
                screen.blit(inc_value_surface,
                            (20, offset + 50))
                screen.blit(inc_weight_surface,
                            (20, offset + 75))

                # Render an edit button for the value and weight
                screen.blit(edit,
                            (135, offset + 50))
                screen.blit(edit,
                            (135, offset + 75))

        # Draw pathway
        for neuron in neurons:
            n_x, n_y = neuron.pos

            # Draw connections
            for connection in neuron.outgoing_connections:
                t_x, t_y = connection.target.pos

                if connection.weight <= 0:
                    # Draw negative connection
                    draw_arrow(screen,
                               pygame.Vector2(graph_scale * n_x + right_shift, graph_scale * n_y),
                               pygame.Vector2(graph_scale * t_x + right_shift, graph_scale * t_y),
                               pygame.Color("red"),
                               2 * abs(connection.weight),
                               16,
                               8)
                else:
                    # Draw positive connection
                    draw_arrow(screen,
                               pygame.Vector2(graph_scale * n_x + right_shift, graph_scale * n_y),
                               pygame.Vector2(graph_scale * t_x + right_shift, graph_scale * t_y),
                               pygame.Color("lightblue"),
                               2 * abs(connection.weight),
                               16,
                               8)

        # Draw neurons
        for neuron in neurons:
            n_x, n_y = neuron.pos
            pygame.draw.circle(screen,
                               (0, 255 * neuron.value, 0),
                               (graph_scale * n_x + right_shift, graph_scale * n_y),
                               6)

        pygame.display.flip()

    pygame.quit()


def display_kgml(kgml_path, model_path, is_generating_model, generated_model_file_name):
    """Parses a KGML file and displays it in an interactive visual form

    Args:
        kgml_path (str): A string that is the file path to a xml KGML file
        model_path (str): A string that is the file path to a txt model file
        is_generating_model (bool): Determines if the application will make a model file
        generated_model_file_name (str): The name of the file that will store your generated model
    """
    neural_network = parse_kgml(kgml_path)
    visualize_network(neural_network, model_path)
    if is_generating_model:
        neural_network.generate_model_file(generated_model_file_name)


if __name__ == "__main__":
    display_kgml("kmgl_files/hsa05224.xml", "", False, "")
