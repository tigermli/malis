from __future__ import print_function
import theano
import theano.tensor as T
import numpy as np
from malis.theano_op import keras_malis, malis_metrics_no_theano
import pdb
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten, Reshape
from keras.layers.convolutional import Convolution3D, MaxPooling2D
from keras.optimizers import SGD
na = np.newaxis

N_SAMPLES = 6
EDG_PER_VOX = 3
VOLUME_SHAPE = (1,5,6,7)
EDGEVOL_SHAPE = (EDG_PER_VOX,) + VOLUME_SHAPE[1:]
DATA_SHAPE = (N_SAMPLES,) + VOLUME_SHAPE

# create some test data
# two objects
gt = np.zeros(DATA_SHAPE, dtype=np.int32)
# first sample
gt[0, 0, :3, ...] = 1
gt[0, 0, 3:, ...] = 2
# second sample
gt[1, 0, :, :3, ...] = 1
gt[1, 0, :, 3:, ...] = 2
# third sample
gt[2, 0, :, :2, ...] = 1
gt[2, 0, :, 2:, ...] = 2
gt[3:] = 3

# create data from gt
data=np.zeros(DATA_SHAPE)
# first sample
data[0, 0, :3, ...] = 1
data[0, 0, 3, ...] = 0
data[0, 0, 4:, ...] = 1
# second sample
data[1, 0, :, :3, ...] = 1
data[1, 0, :, 3, ...] = 0
data[1, 0, :, 4:, ...] = 1
# third sample
data[2, 0, :, :2, ...] = 1
data[2, 0, :, 2, ...] = 0
data[2, 0, :, 3:, ...] = 1
data[3:] = 1


# add some noise
data += np.random.normal(loc=0, scale=.01, size=DATA_SHAPE)

# start building classifier
eta = 0.1 #learning rate
n_epochs = 20
iterations_per_epoch = 100
keras_malis_loss = keras_malis(VOLUME_SHAPE[1:])

# start network creation
model = Sequential()
model.add(Convolution3D(nb_filter=5,
                        kernel_dim1=3,
                        kernel_dim2=3,
                        kernel_dim3=3,
                        input_shape=VOLUME_SHAPE,
                        border_mode="same"))
model.add(Activation("relu"))
model.add(Convolution3D(nb_filter=5,
                        kernel_dim1=3,
                        kernel_dim2=3,
                        kernel_dim3=3,
                        input_shape=VOLUME_SHAPE,
                        border_mode="same"))
model.add(Activation("relu"))
model.add(Convolution3D(nb_filter=3,
                        kernel_dim1=3,
                        kernel_dim2=3,
                        kernel_dim3=3,
                        input_shape=VOLUME_SHAPE,
                        border_mode="same"))
model.add(Activation("sigmoid"))
sgd = SGD(lr=eta, momentum=0.4, nesterov=True)
model.compile(optimizer="SGD",
              loss=keras_malis_loss)
loss_history = np.empty((n_epochs))
for epoch in range(n_epochs):
    for i in range(iterations_per_epoch):
        # train
        training_hist = model.fit(data,
                                gt,
                                batch_size=1,
                                nb_epoch=1,
                                verbose=0)
    # evaluate
    pred = model.predict(data)
    returndict = malis_metrics_no_theano(N_SAMPLES, VOLUME_SHAPE[1:], pred, gt)
    print(returndict["malis_cost"])
    loss_history[epoch] = returndict["malis_cost"]

plt.figure()
plt.plot(loss_history)
plt.xlabel("epochs")
plt.ylabel("training loss")



# predict an affinity graph and compare it with the affinity graph
# created by the true segmentation
plot_sample = 1
from malis import mknhood3d, seg_to_affgraph
pred_aff = model.predict(data)[plot_sample]
aff = seg_to_affgraph(gt[plot_sample,0], mknhood3d())
plt.figure()
plt.subplot(131)
plt.pcolor(data[plot_sample,0,1], cmap="gray")
plt.title("data")
plt.subplot(132)
plt.pcolor(aff[1,1], cmap="gray")
plt.title("aff from gt")
plt.subplot(133)
plt.pcolor(pred_aff[1,1], cmap="gray")
plt.title("predicted aff")
plt.show()
