"""
TEACHBOT Offline Knowledge Base

A lookup table of (triggers, answer) pairs used by the offline rule parser
when no cloud LLM (Gemini/OpenAI) is available or has failed.

Structure: each entry is (triggers, reply_text)
  - triggers: a list of words/phrases. If a trigger is short (<=4 characters,
    e.g. "ac", "led", "gpio"), it's matched as a WHOLE WORD only, to avoid
    false matches (e.g. "dc" incorrectly matching inside "adc").
  - Longer triggers are matched as substrings, same as the original code.

To add a new topic: just append a new (triggers, reply_text) tuple to
ACADEMIC_KB below. No other code changes needed.
"""

from typing import List, Optional, Tuple

ACADEMIC_KB: List[Tuple[List[str], str]] = [

    # ---------- BASIC ELECTRICAL QUANTITIES ----------
    (["what is current", "electric current"], "Electric current is the rate of flow of electric charge through a conductor, measured in Amperes, symbol I."),
    (["what is voltage"], "Voltage is the electrical potential difference between two points that drives current through a circuit, measured in Volts."),
    (["what is resistance"], "Resistance is the opposition a material offers to the flow of electric current, measured in Ohms, symbol R."),
    (["what is power", "electrical power"], "Electrical power is the rate at which electrical energy is transferred, calculated as P equals V times I, measured in Watts."),
    (["what is energy"], "Energy is the capacity to do work, measured in Joules. Electrical energy equals power multiplied by time."),
    (["what is charge", "electric charge"], "Electric charge is a fundamental property of matter that causes it to experience a force in an electric field, measured in Coulombs."),
    (["what is a conductor", "what is conductor"], "A conductor is a material, like copper, that allows electric current to flow easily due to loosely bound electrons."),
    (["what is an insulator", "what is insulator"], "An insulator is a material, like rubber or glass, that resists the flow of electric current."),
    (["what is emf", "electromotive force"], "EMF, or electromotive force, is the energy provided by a source like a battery per unit charge, measured in Volts."),
    (["what is frequency"], "Frequency is the number of complete cycles of a periodic signal that occur per second, measured in Hertz."),

    # ---------- LAWS AND NETWORK THEOREMS ----------
    (["ohm law", "ohms law"], "Ohm's Law states that current through a conductor is directly proportional to voltage across it: V = I times R."),
    (["kirchhoff", "kcl", "kvl"], "Kirchhoff's Current Law states current entering a junction equals current leaving it. Kirchhoff's Voltage Law states voltages around a closed loop sum to zero."),
    (["superposition theorem"], "The Superposition Theorem states that in a linear circuit with multiple sources, the response at any point equals the sum of responses caused by each source acting alone."),
    (["thevenin"], "Thevenin's Theorem lets you replace a complex linear circuit with a single voltage source and series resistance, as seen from two output terminals."),
    (["norton"], "Norton's Theorem replaces a complex linear circuit with a single current source in parallel with a resistance, as seen from two output terminals."),
    (["maximum power transfer"], "The Maximum Power Transfer Theorem states maximum power is delivered to a load when the load resistance equals the source's internal resistance."),
    (["reciprocity theorem"], "The Reciprocity Theorem states that in a linear bilateral network, the ratio of response to excitation stays the same even if their positions are interchanged."),
    (["millman"], "Millman's Theorem simplifies circuits with multiple parallel voltage sources into a single equivalent voltage source."),
    (["star delta", "delta star"], "Star-Delta transformation converts a star-connected network of resistors into an equivalent delta-connected network, or vice versa, for easier circuit analysis."),
    (["faraday law", "faradays law"], "Faraday's Law of Induction states that a changing magnetic field induces an electromotive force in a nearby conductor."),

    # ---------- CIRCUIT ELEMENTS ----------
    (["what is a resistor", "what is resistor"], "A resistor is a passive component that limits or controls the flow of electric current in a circuit."),
    (["what is a capacitor", "what is capacitor", "capacit"], "A capacitor stores electrical energy in an electric field, with capacitance C equal to charge Q divided by voltage V, measured in Farads."),
    (["what is an inductor", "what is inductor"], "An inductor stores energy in a magnetic field when current flows through it, measured in Henrys."),
    (["resistors in series", "series resistor"], "In series, resistances simply add: R total equals R1 plus R2 plus R3, and so on."),
    (["resistors in parallel", "parallel resistor"], "In parallel, reciprocals add: 1 over R total equals 1 over R1 plus 1 over R2, giving a total always smaller than the smallest resistor."),
    (["capacitors in series"], "Capacitors in series combine like resistors in parallel: 1 over C total equals 1 over C1 plus 1 over C2."),
    (["capacitors in parallel"], "Capacitors in parallel simply add: C total equals C1 plus C2 plus C3."),
    (["rc circuit"], "An RC circuit combines a resistor and capacitor, commonly used for filtering, timing, and charge/discharge behavior."),
    (["rl circuit"], "An RL circuit combines a resistor and inductor, used in filters and to study current growth and decay."),
    (["rlc circuit"], "An RLC circuit combines a resistor, inductor, and capacitor, and can exhibit resonance at a specific frequency."),

    # ---------- AC FUNDAMENTALS ----------
    (["difference between ac and dc", "ac vs dc", "ac and dc"], "AC, alternating current, periodically reverses direction, like household mains power. DC, direct current, flows in one constant direction, like a battery."),
    (["what is amplitude"], "Amplitude is the maximum value or height of a waveform, representing its peak magnitude."),
    (["rms value", "what is rms"], "RMS, or Root Mean Square, value is the effective value of an AC waveform that would deliver the same power as an equivalent DC value."),
    (["peak value"], "The peak value of an AC waveform is its maximum instantaneous value, reached once each cycle."),
    (["what is phase"], "Phase describes the position of a waveform in its cycle at a given moment, usually measured in degrees relative to a reference."),
    (["what is impedance"], "Impedance is the total opposition a circuit offers to AC current, combining resistance and reactance, measured in Ohms."),
    (["what is reactance"], "Reactance is the opposition to current flow caused by capacitors or inductors in an AC circuit, measured in Ohms."),
    (["what is resonance"], "Resonance occurs in an RLC circuit when inductive and capacitive reactances cancel out, maximizing current at a specific frequency."),
    (["power factor"], "Power factor is the ratio of real power used by a circuit to the apparent power supplied, indicating how efficiently electrical power is being used."),
    (["three phase", "3 phase"], "Three-phase power uses three alternating currents offset by 120 degrees, commonly used for efficient industrial power transmission."),

    # ---------- SEMICONDUCTOR DEVICES ----------
    (["what is a semiconductor", "semiconductor"], "A semiconductor is a material like silicon with conductivity between a conductor and insulator, forming the basis of diodes, transistors, and microchips."),
    (["what is a diode", "what is diode"], "A diode is a semiconductor device that allows current to flow easily in one direction while blocking the reverse direction."),
    (["zener diode"], "A Zener diode is a special diode designed to allow reverse current flow at a specific breakdown voltage, commonly used for voltage regulation."),
    (["what is led", "light emitting diode"], "An LED, or Light Emitting Diode, emits light when current flows through it in the forward direction."),
    (["what is a transistor", "what is transistor"], "A transistor is a semiconductor device used to amplify or switch electronic signals, forming the building block of modern electronics."),
    (["what is bjt", "bipolar junction transistor"], "A BJT, Bipolar Junction Transistor, is a current-controlled transistor with three terminals: base, collector, and emitter."),
    (["what is fet", "field effect transistor"], "An FET, Field Effect Transistor, is a voltage-controlled transistor that uses an electric field to control current flow."),
    (["what is mosfet"], "A MOSFET is a type of FET widely used for switching and amplification, known for high efficiency and fast switching speeds."),
    (["what is scr", "silicon controlled rectifier"], "An SCR, Silicon Controlled Rectifier, is a semiconductor device used to control large amounts of power using a small trigger signal."),
    (["photodiode"], "A photodiode is a semiconductor device that converts light into an electrical current, commonly used in light sensors."),

    # ---------- DIGITAL ELECTRONICS ----------
    (["logic gate"], "A logic gate is a basic building block of digital circuits that performs a logical operation on one or more binary inputs."),
    (["and gate"], "An AND gate outputs 1 only when all of its inputs are 1; otherwise it outputs 0."),
    (["or gate"], "An OR gate outputs 1 if at least one of its inputs is 1."),
    (["not gate"], "A NOT gate, or inverter, outputs the opposite of its single input: 1 becomes 0, and 0 becomes 1."),
    (["nand gate"], "A NAND gate is an AND gate followed by a NOT gate, outputting 0 only when all inputs are 1."),
    (["flip flop"], "A flip-flop is a digital circuit that stores one bit of data, forming the basis of memory and sequential logic circuits."),
    (["binary number", "binary system"], "The binary number system uses only two digits, 0 and 1, and is the fundamental language of digital electronics and computers."),
    (["multiplexer"], "A multiplexer selects one of several input signals and forwards it to a single output line, based on control signals."),
    (["demultiplexer"], "A demultiplexer takes a single input signal and routes it to one of several output lines, based on control signals."),
    (["adder circuit", "half adder", "full adder"], "An adder circuit performs binary addition. A half adder adds two bits; a full adder adds two bits plus a carry-in from a previous stage."),

    # ---------- MICROCONTROLLERS / EMBEDDED SYSTEMS ----------
    (["what is a microcontroller", "what is microcontroller"], "A microcontroller is a compact integrated circuit containing a processor, memory, and input/output peripherals, used to control electronic devices."),
    (["what is a microprocessor", "what is microprocessor"], "A microprocessor is the central processing unit of a computer system, handling instructions and calculations, but needs external memory and peripherals unlike a microcontroller."),
    (["what is arduino"], "Arduino is an open-source microcontroller platform widely used for prototyping electronics projects, programmed using a simplified version of C plus plus."),
    (["what is raspberry pi"], "Raspberry Pi is a small, affordable single-board computer capable of running a full operating system, commonly used in robotics and embedded projects like me."),
    (["what is esp32", "esp 32"], "The ESP32 is a low-cost microcontroller with built-in Wi-Fi and Bluetooth, widely used for IoT and embedded control tasks."),
    (["what is gpio"], "GPIO stands for General Purpose Input Output, referring to programmable pins on a microcontroller that can read sensors or control devices."),
    (["what is pwm"], "PWM, Pulse Width Modulation, is a technique for controlling power delivered to a device by rapidly switching it on and off, controlling motor speed or LED brightness."),
    (["what is adc", "analog to digital"], "An ADC, Analog to Digital Converter, converts a continuous analog signal, like a sensor voltage, into a digital value a microcontroller can process."),
    (["what is uart"], "UART, Universal Asynchronous Receiver Transmitter, is a common serial communication protocol used to send data between microcontrollers and other devices."),
    (["what is i2c", "what is spi"], "I2C and SPI are serial communication protocols used to connect microcontrollers to sensors and peripherals, using two or four wires respectively."),

    # ---------- COMMUNICATION SYSTEMS ----------
    (["what is modulation"], "Modulation is the process of varying a carrier signal to encode information for transmission, commonly used in radio and wireless communication."),
    (["what is am", "amplitude modulation"], "Amplitude Modulation, AM, varies the amplitude of a carrier wave to encode information, commonly used in AM radio broadcasting."),
    (["what is fm", "frequency modulation"], "Frequency Modulation, FM, varies the frequency of a carrier wave to encode information, offering better sound quality than AM."),
    (["analog signal", "digital signal"], "An analog signal varies continuously over time, while a digital signal represents information using discrete binary values, 0s and 1s."),
    (["what is bandwidth"], "Bandwidth is the range of frequencies a communication channel can carry, directly affecting how much data can be transmitted."),
    (["what is an antenna", "what is antenna"], "An antenna is a device that converts electrical signals into electromagnetic waves for transmission, or receives them and converts them back."),
    (["what is wifi", "what is wi-fi"], "Wi-Fi is a wireless networking technology that lets devices connect to the internet or communicate with each other using radio waves."),
    (["what is bluetooth"], "Bluetooth is a short-range wireless technology used for connecting devices like headphones, sensors, and controllers without cables."),
    (["sampling theorem", "nyquist"], "The Sampling Theorem states a signal must be sampled at least twice its highest frequency component to be accurately reconstructed, known as the Nyquist rate."),
    (["what is noise"], "In electronics, noise refers to unwanted random variations in a signal that can distort or interfere with the intended information."),

    # ---------- CONTROL SYSTEMS ----------
    (["what is a control system", "what is control system"], "A control system manages, commands, or regulates the behavior of other devices or systems using feedback or predefined logic."),
    (["open loop", "closed loop"], "An open-loop system operates without feedback, while a closed-loop system uses feedback to compare actual output against a desired target and correct errors."),
    (["what is feedback"], "Feedback is the process of returning part of a system's output back as input, used to regulate and stabilize system behavior."),
    (["pid controller", "what is pid"], "A PID controller uses Proportional, Integral, and Derivative terms to continuously calculate an error and adjust a control output to minimize it."),
    (["transfer function"], "A transfer function represents the relationship between a system's input and output in the frequency domain, used to analyze system behavior."),
    (["what is stability", "system stability"], "In control systems, stability means a system's output remains bounded and predictable in response to a bounded input, without growing uncontrollably."),
    (["what is a sensor", "what is sensor"], "A sensor is a device that detects and measures a physical property, like light, distance, or temperature, and converts it into an electrical signal."),
    (["what is an actuator", "what is actuator"], "An actuator is a device that converts an electrical signal into physical motion or action, such as a motor or servo."),
    (["what is a transducer", "what is transducer"], "A transducer converts one form of energy into another, such as converting sound into an electrical signal, as in a microphone."),
    (["what is a servo motor", "what is servo"], "A servo motor is a motor combined with a feedback sensor that allows precise control of its position, speed, or angle."),

    # ---------- PHYSICS / MECHANICS ----------
    (["newton law", "newtons law"], "Newton's three laws of motion: an object stays at rest or in motion unless acted on by a force; force equals mass times acceleration; every action has an equal and opposite reaction."),
    (["what is force"], "Force is a push or pull acting on an object, causing it to accelerate, calculated as F equals mass times acceleration, measured in Newtons."),
    (["mass and weight", "difference between mass and weight"], "Mass is the amount of matter in an object, measured in kilograms, while weight is the force of gravity acting on that mass, measured in Newtons."),
    (["what is work", "work done"], "In physics, work is done when a force causes displacement of an object, calculated as force multiplied by distance moved in the direction of the force."),
    (["what is friction"], "Friction is the resistive force that opposes relative motion between two surfaces in contact."),
    (["what is velocity"], "Velocity is the rate of change of an object's position with respect to time, including both speed and direction."),
    (["what is acceleration"], "Acceleration is the rate of change of velocity with respect to time, measured in meters per second squared."),
    (["what is momentum"], "Momentum is the product of an object's mass and velocity, representing the quantity of motion it has."),
    (["law of conservation of energy"], "The Law of Conservation of Energy states that energy cannot be created or destroyed, only converted from one form to another."),
    (["what is gravity"], "Gravity is the force of attraction between any two masses, and on Earth it gives objects weight and causes them to fall toward the ground."),

    # ---------- ROBOTICS SPECIFIC ----------
    (["what is a robot", "what is robot"], "A robot is a programmable machine capable of carrying out tasks autonomously or semi-autonomously, often using sensors, actuators, and a control system."),
    (["what is slam"], "SLAM stands for Simultaneous Localization and Mapping. It's how I build a map of an unknown environment while tracking my own position within it, using sensors like LiDAR."),
    (["what is nav2", "navigation stack"], "Nav2 is the navigation system I use to plan safe paths and avoid obstacles while moving autonomously between locations."),
    (["what is lidar"], "LiDAR uses laser pulses to measure distances to nearby objects, letting me build a map of my surroundings and detect obstacles."),
    (["autonomous navigation"], "Autonomous navigation means a robot can move from one point to another on its own, using sensors, mapping, and path planning without manual control."),
    (["degrees of freedom", "what is dof"], "Degrees of freedom refers to the number of independent ways a mechanical system, like a robotic arm, can move."),
    (["what is a gripper", "what is gripper"], "A gripper is the end effector of a robotic arm used to grasp, hold, or manipulate objects."),
    (["obstacle avoidance"], "Obstacle avoidance is a robot's ability to detect obstacles in its path using sensors and automatically adjust its route to avoid collisions."),
    (["path planning"], "Path planning is the process of calculating the best route for a robot to travel from a starting point to a destination while avoiding obstacles."),
    (["what is odometry"], "Odometry estimates a robot's change in position over time using data from wheel encoders, helping track how far and in what direction it has moved."),

    # ---------- GENERAL / MISC ----------
    (["what is engineering"], "Engineering is the application of scientific and mathematical principles to design, build, and improve structures, machines, and systems."),
    (["what is iot", "internet of things"], "IoT, the Internet of Things, refers to everyday physical devices connected to the internet, able to collect and exchange data."),
    (["what is ai", "artificial intelligence"], "Artificial Intelligence is the field of building systems that can perform tasks normally requiring human intelligence, like understanding language or recognizing images."),
    (["machine learning"], "Machine learning is a branch of AI where systems learn patterns from data to make predictions or decisions, without being explicitly programmed for every case."),
    (["cloud computing"], "Cloud computing means running software and storing data on remote servers accessed over the internet, rather than on a local device."),
    (["what is an api", "what is api"], "An API, Application Programming Interface, is a defined way for two software systems to communicate and exchange data with each other."),
    (["what is a database", "what is database"], "A database is an organized collection of data stored electronically, structured so it can be easily accessed, managed, and updated."),
    (["what is python"], "Python is a popular, easy-to-read programming language widely used for web development, data science, automation, and robotics, including much of my own backend."),
    (["what is a circuit", "what is circuit"], "A circuit is a closed path through which electric current can flow, made up of components like resistors, sources, and conductors."),
    (["what is a battery", "what is battery"], "A battery is a device that stores chemical energy and converts it into electrical energy to power a circuit."),
]


def lookup_academic_kb(cleaned_text: str) -> Optional[str]:
    """
    Searches the knowledge base for a matching topic.
    Short triggers (<=4 chars) are matched as whole words only,
    to avoid accidental substring matches (e.g. 'dc' inside 'adc').
    Returns the matching reply_text, or None if nothing matched.
    """
    words = set(cleaned_text.split())

    for triggers, reply_text in ACADEMIC_KB:
        for trigger in triggers:
            if len(trigger) <= 4 and " " not in trigger:
                if trigger in words:
                    return reply_text
            else:
                if trigger in cleaned_text:
                    return reply_text
    return None
