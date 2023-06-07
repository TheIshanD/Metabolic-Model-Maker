"""Defines the foundation to create a neural network structure"""
from math import tanh


class NeuralNetwork:
    """Represents a network of neurons and holds operations on full network"""

    def __init__(self):
        self.neurons = {}

    def setup(self, model_path):
        """Sets the neural network up for computation"""
        if model_path == "":
            # If a model path is not given, set all neuron values to 0.5
            for neuron in self.neurons.values():
                if len(neuron.incoming_connections) == 0:
                    neuron.is_input = True
                    neuron.value = 0.5
        else:
            # If a model path is given , use that file to generate representation
            self.input_model_file(model_path)

    def propagate_net(self):
        """Propagates the network by 1 step"""

        for _ in range(1):

            # Set up a visited array that is initialized all to false
            visited = {}
            for id_, neuron in self.neurons.items():
                visited[id_] = False

            # Iterate through all the neurons and compute their new values for the next propagation
            for id_, neuron in self.neurons.items():
                if visited[id_]:
                    continue

                visited[id_] = True

                # Add up the computations of all the inputting neurons to determine effect and process decay
                connection_sum = 0
                for conn in neuron.incoming_connections:
                    connection_sum += conn.source.value * conn.weight
                connection_sum += neuron.bias
                connection_sum += neuron.value/neuron.decay

                # Use Activation Function on the sum of all input computations
                neuron.next_propagation_value = neuron.activation_function(connection_sum)

                # If node is an input value, hold the value constant (it is an environment variable)
                if len(neuron.incoming_connections) == 0:
                    neuron.next_propagation_value = neuron.value

            # Puts in the newly computed values into the existing network
            for id_, neuron in self.neurons.items():
                neuron.value = neuron.next_propagation_value

    def input_model_file(self, model_path):
        """Sets the neural network up based on given model file"""

        file = open(model_path, "r", encoding="utf8")

        # Read in the values and biases of the nodes
        num_vals = int(file.readline())
        file.readline()
        for _ in range(num_vals):
            line = file.readline().split(",")

            for neuron in self.neurons.values():
                if neuron.code == line[0]:
                    neuron.value = float(line[1])
                    neuron.bias = float(line[2])

        file.readline()

        # Read in the weights of the connections between nodes
        num_conns = int(file.readline())
        file.readline()
        for _ in range(num_conns):
            line = file.readline().split(",")

            for neuron in self.neurons.values():
                if neuron.code == line[1]:
                    for conn in neuron.incoming_connections:
                        if conn.source.code == line[0]:
                            conn.weight = float(line[2])

        file.close()

    def generate_model_file(self, generated_model_file_name):
        """Generate a model file based on a neural network"""

        file = open(generated_model_file_name, "w", encoding="utf8")

        # Generate a list of neurons and their values/biases
        file_string = ""
        neuron_codes = set()
        neurons_string = ""
        for neuron in self.neurons.values():
            if not neuron.code in neuron_codes:
                neurons_string += (neuron.code + ","
                                   + str(neuron.value) + ","
                                   + str(neuron.bias) + ",\n")
                neuron_codes.add(neuron.code)

        # Generate a list of connections and their weights
        conn_weights = {}
        for neuron in self.neurons.values():
            for conn in neuron.incoming_connections:
                conn_weights[conn.source.code + "," + conn.target.code] = conn.weight

        # Print generated output
        file_string += (str(len(neuron_codes)) + "\n")
        file_string += ("code val bias" + "\n")
        file_string += neurons_string
        file_string += ("\n")
        file_string += (str(len(conn_weights)) + "\n")
        file_string += ("src target weight" + "\n")

        # Print connections list
        for conn_description, weight in conn_weights.items():
            file_string += (conn_description + "," + str(weight) + ",\n")

        file.write(file_string)
        file.close()


class Neuron:
    """Can compute values and connect with other Neurons"""

    def __init__(self, id_, name, type_, pos, code):
        # Define properties useful for general purpose handling
        self.id_ = id_
        self.name = name
        self.type = type_
        self.outgoing_connections = []
        self.incoming_connections = []
        self.pos = pos
        self.next_propagation_value = 1
        self.code = code
        self.is_input = False

        # Define properties useful for calculation
        self.decay = 2.0
        self.value = 0.5
        self.bias = 0.0
        self.activation_type = "tanh(relu())"

    def connect(self, target_neuron, weight):
        """Connects Neuron with another Neuron"""
        connection = Connection(self, target_neuron, weight)
        self.outgoing_connections.append(connection)
        target_neuron.incoming_connections.append(connection)

    def activation_function(self, connection_sum):
        """Non-linearly transforms the sum of connections in the neuron"""
        # Define the activation function as tanh(relu())
        return tanh(max(0, connection_sum))


class Connection:
    """Can connect two Neurons"""

    def __init__(self, source, target, weight):
        self.source = source
        self.target = target
        self.weight = float(weight)
