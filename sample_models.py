from keras import backend as K
from keras.models import Model
from keras.layers import (BatchNormalization, Conv1D, Dense, Input,
    TimeDistributed, Activation, Bidirectional, SimpleRNN, GRU, LSTM)

def simple_rnn_model(input_dim, output_dim=29):
    """ Build a recurrent network for speech
    """
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # Add recurrent layer
    simp_rnn = GRU(output_dim, return_sequences=True,
                 implementation=2, name='rnn')(input_data)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(simp_rnn)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: x
    print(model.summary())
    return model

def rnn_model(input_dim, units, activation, output_dim=29):
    """ Build a recurrent network for speech
    """
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # Add recurrent layer
    simple_rnn = GRU(units, activation=activation,
        return_sequences=True, implementation=2, name='rnn')(input_data)
    # TODO: Add batch normalization
    bn_rnn = BatchNormalization()(simple_rnn)
    # TODO: Add a TimeDistributed(Dense(output_dim)) layer
    time_dense = TimeDistributed(Dense(output_dim))(bn_rnn)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(time_dense)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: x
    print(model.summary())
    return model


def cnn_rnn_model(input_dim, filters, kernel_size, conv_stride,
    conv_border_mode, units, output_dim=29):
    """ Build a recurrent + convolutional network for speech
    """
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # Add convolutional layer
    conv_1d = Conv1D(filters, kernel_size,
                     strides=conv_stride,
                     padding=conv_border_mode,
                     activation='relu',
                     name='conv1d')(input_data)
    # Add batch normalization
    bn_cnn = BatchNormalization(name='bn_conv_1d')(conv_1d)
    # Add a recurrent layer
    simple_rnn = SimpleRNN(units, activation='relu',
        return_sequences=True, implementation=2, name='rnn')(bn_cnn)
    # TODO: Add batch normalization
    bn_rnn = BatchNormalization()(simple_rnn)
    # TODO: Add a TimeDistributed(Dense(output_dim)) layer
    time_dense = TimeDistributed(Dense(output_dim))(bn_rnn)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(time_dense)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: cnn_output_length(
        x, kernel_size, conv_border_mode, conv_stride)
    print(model.summary())
    return model

def cnn_output_length(input_length, filter_size, border_mode, stride,
                       dilation=1):
    """ Compute the length of the output sequence after 1D convolution along
        time. Note that this function is in line with the function used in
        Convolution1D class from Keras.
    Params:
        input_length (int): Length of the input sequence.
        filter_size (int): Width of the convolution kernel.
        border_mode (str): Only support `same` or `valid`.
        stride (int): Stride size used in 1D convolution.
        dilation (int)
    """
    if input_length is None:
        return None
    assert border_mode in {'same', 'valid'}
    dilated_filter_size = filter_size + (filter_size - 1) * (dilation - 1)
    if border_mode == 'same':
        output_length = input_length
    elif border_mode == 'valid':
        output_length = input_length - dilated_filter_size + 1
    return (output_length + stride - 1) // stride

def deep_rnn_model(input_dim, units, recur_layers, output_dim=29):
    """ Build a deep recurrent network for speech
    """
    def recurrent_layer(prev_layer, name):
        layer = GRU(units=units,
                    return_sequences=True,
                    implementation=2,
                    name=name
        )(prev_layer)
        return BatchNormalization()(layer)
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # TODO: Add recurrent layers, each with batch normalization
    gru_rnn = input_data
    for i in range(recur_layers):
        gru_rnn = recurrent_layer(gru_rnn, name="rnn_{}".format(i))
    # TODO: Add batch normalization
    bn_rnn = BatchNormalization()(gru_rnn)
    # TODO: Add a TimeDistributed(Dense(output_dim)) layer
    time_dense = TimeDistributed(Dense(output_dim))(bn_rnn)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(time_dense)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: x
    print(model.summary())
    return model

def bidirectional_rnn_model(input_dim, units, output_dim=29):
    """ Build a bidirectional recurrent network for speech
    """
    # Main acoustic input
    input_data = Input(name='the_input', shape=(None, input_dim))
    # TODO: Add bidirectional recurrent layer
    bidir_rnn = Bidirectional(
        GRU(units=units,
            return_sequences=True,
            implementation=2,
            name='rnn'
        )
    )(input_data)
    # TODO: Add a TimeDistributed(Dense(output_dim)) layer
    time_dense = TimeDistributed(Dense(output_dim))(bidir_rnn)
    # Add softmax activation layer
    y_pred = Activation('softmax', name='softmax')(time_dense)
    # Specify the model
    model = Model(inputs=input_data, outputs=y_pred)
    model.output_length = lambda x: x
    print(model.summary())
    return model

def final_model(cnn_filters, cnn_kernel_size, cnn_strides, cnn_padding,
                rnn_units, rnn_dropout, rnn_recurrent_dropout,
                rnn_layer_count, input_dim=161, output_dim=29):
    """ Build a deep network for speech
    """
    def output_length(x):
        return cnn_output_length(
            x, cnn_kernel_size, cnn_padding, cnn_strides
        )
    def rnn_layer(layer, number):
        layer = Bidirectional(
            name='bd_rnn_{}'.format(number),
            layer=GRU(
                units=rnn_units,
                return_sequences=True,
                implementation=2,
                name='rnn_{}'.format(number),
                dropout=rnn_dropout,
                recurrent_dropout=rnn_recurrent_dropout
            )
        )(layer)
        return BatchNormalization(name='bn_rnn_{}'.format(number))(layer)
    # Main acoustic input
    inputs = Input(name='the_input', shape=(None, input_dim))
    # TODO: Specify the layers in your network
    outputs = Conv1D(
        filters=cnn_filters,
        kernel_size=cnn_kernel_size,
        strides=cnn_strides,
        padding=cnn_padding,
        activation='relu',
        name='conv_1d'
    )(inputs)
    outputs = BatchNormalization(name='bn_conv_1d')(outputs)
    for i in range(rnn_layer_count):
        outputs = rnn_layer(number=i, layer=outputs)
    outputs = TimeDistributed(
        name='td_dense',
        layer=Dense(units=output_dim, name='dense')
    )(outputs)
    # TODO: Add softmax activation layer
    outputs = Activation('softmax', name='softmax')(outputs)
    # Specify the model
    model = Model(inputs=inputs, outputs=outputs)
    # TODO: Specify model.output_length
    model.output_length = output_length
    print(model.summary())
    return model
