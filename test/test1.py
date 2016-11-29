import os
import h5py
import numpy as np
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.layers import Activation, Dropout, Flatten, Dense
from sklearn.model_selection import train_test_split
from sklearn.utils import column_or_1d
from keras.optimizers import SGD,RMSprop
from keras.regularizers import l2
from keras.utils import np_utils
from sklearn import svm

from sklearn.metrics import classification_report,confusion_matrix
import matplotlib.pyplot as plt
import matplotlib
import os

try:
    import cPickle as pickle
except:
    import pickle

seed = 7
np.random.seed(seed)
# path to the model weights file.
weights_path = '../dataset/vgg16_weights.h5'
top_model_weights_path = 'bottleneck_fc_model.h5'
f_model = './model'
# dimensions of our images.
img_width, img_height = 150, 150
nb_classes = 10

nb_train_samples = 1500
nb_validation_samples = 500
nb_epoch = 2

def load_data():
    # load your data using this function
    f = open("../dataset/myfood10-224.pkl", 'rb')
    d = pickle.load(f)
    data = d['trainFeatures']
    labels = d['trainLabels']
    lz = d['labels']
    data = data.reshape(data.shape[0], 3, 224, 224)
    #data = data.transpose(0, 2, 3, 1)

    return data,labels,lz

def save_bottlebeck_features(X_train, X_test, y_train, y_test):
    datagen = ImageDataGenerator(rescale=1./255)

    model = Sequential()
    model.add(ZeroPadding2D((1,1),input_shape=(3,224,224)))
    model.add(Convolution2D(64, 3, 3, activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(64, 3, 3, activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(128, 3, 3, activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(128, 3, 3, activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(256, 3, 3, activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(256, 3, 3, activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(256, 3, 3, activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu'))
    model.add(ZeroPadding2D((1,1)))
    model.add(Convolution2D(512, 3, 3, activation='relu'))
    model.add(MaxPooling2D((2,2), strides=(2,2)))

    model.add(Flatten())
    model.add(Dense(4096, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(4096, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(1000, activation='softmax'))

    # load the weights of the VGG16 networks
    # (trained on ImageNet, won the ILSVRC competition in 2014)
    # note: when there is a complete match between your model definition
    # and your weight savefile, you can simply call model.load_weights(filename)
    model.load_weights('../dataset/vgg16_weights.h5')
    print('Model loaded.')

    model.pop()
    model.pop()

    bottleneck_features_train = model.predict(X_train, batch_size=32)
    np.save(open('bottleneck_features_train.npy', 'wb'), bottleneck_features_train)


    bottleneck_features_validation = model.predict(X_test, batch_size=32)
    np.save(open('bottleneck_features_validation.npy', 'wb'), bottleneck_features_validation)


def train_top_model(y_train, y_test):
    train_data = np.load(open('bottleneck_features_train.npy' , 'rb'))
    #train_labels = np.array([0] * (nb_train_samples / 2) + [1] * (nb_train_samples / 2))


    validation_data = np.load(open('bottleneck_features_validation.npy', 'rb'))
    #validation_labels = np.array([0] * (nb_validation_samples / 2) + [1] * (nb_validation_samples / 2))

    print train_data.shape
    print validation_data.shape

    model = Sequential()
    model.add(Flatten(input_shape=train_data.shape[1:]))
    model.add(Dense(256, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(10, activation='softmax'))

    rms = RMSprop(lr=5e-4, rho=0.9, epsilon=1e-08, decay=0.01)

    model.compile(optimizer=rms,
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    model.fit(train_data, y_train,
          nb_epoch=50, batch_size=32,
          validation_data=(validation_data, y_test))

    model.save_weights(top_model_weights_path)
    json_string = model.to_json()
    open(os.path.join(f_model,'test_model.json'), 'w').write(json_string)

    y_proba = model.predict(validation_data)
    y_pred = np_utils.probas_to_classes(y_proba)
    target_names = ['class 0(BIKES)', 'class 1(CARS)', 'class 2(HORSES)','3','3','3','3','3','3','3']
    print(classification_report(np.argmax(y_test,axis=1), y_pred,target_names=target_names))
    print(confusion_matrix(np.argmax(y_test,axis=1), y_pred))

    '''
    print "Training SVM.."
    clf = svm.SVC(kernel='rbf', gamma=0.7, C=1.0)

    clf.fit(train_data, y_train.ravel())
    #y_pred = clf.predict(test_data)
    score = clf.score(validation_data, y_test.ravel())
    print score
    '''

if __name__ == "__main__":
    print "Loading data.."
    data, labels, lz = load_data()
    data = data.astype('float32')
    data /= 255
    lz = np.array(lz)
    print "Data loaded !"

    X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.15, random_state=seed)
    print X_train.shape
    print X_test.shape
    print "Test train splitted !"

    #save_bottlebeck_features(X_train, X_test, y_train, y_test)
    train_top_model(y_train, y_test)