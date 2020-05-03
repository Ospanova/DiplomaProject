import numpy as np
import pandas as pd
import scipy.optimize

from api.models import Myrating, Movie


def recommender():
    def normalize_ratings(Y, R):
        """
        Preprocess data by subtracting mean rating
        normalized Y so that each movie
        has a rating of 0 on average, and returns the mean rating in Ymean
        """
        Ymean = np.zeros((Y.shape[0], 1))
        Ynorm = np.zeros(Y.shape)

        for i in range(Y.shape[0]):
            rated = R[i, :] == 1
            Ymean[i] = np.mean(Y[i, rated])
            Ynorm[i, rated] = Y[i, rated] - Ymean[i]

        return Ynorm, Ymean

    def flatten_params(X, Theta):
        # merge X and Theta to params
        return np.concatenate((X.flatten(), Theta.flatten()))

    def reshape_params(params, number_of_movies, number_of_users, number_of_features):
        """
        unfold X and theta from params
        """
        total_length =  number_of_movies * number_of_features + number_of_users * number_of_features
        assert params.shape[0] == total_length

        X = params[:number_of_movies * number_of_features].reshape((number_of_movies, number_of_features))

        Theta = params[number_of_movies * number_of_features:].reshape((number_of_users, number_of_features))

        return X, Theta

    def cofi_cost_func(params, Y, R, number_of_users, number_of_movies, number_of_features, lambd):
        """
        1) computing the estimated rating for all pairs (user, movie)
        2) computing the difference = estimated - real_rating for movies that are rated
        """
        X, Theta = reshape_params(params, number_of_movies, number_of_users, number_of_features)

        Y_est = np.dot(X, np.transpose(Theta))

        Y_err = (Y_est - Y) * R

        #cost_function
        J = 0.5 * np.sum(np.square(Y_err))

        # for regularization
        J += (lambd / 2.) * (np.sum(np.square(Theta)) + np.sum(np.square(X)))
        return J

    def cofi_grad(myparams, Y, R, number_of_users, number_of_movies, number_of_features, lambd):
        """
        Note that the function returns the gradient for both sets of variables by unrolling them into a single vector
        """
        X, Theta = reshape_params(myparams, number_of_movies, number_of_users, number_of_features)

        Y_est = np.dot(X, np.transpose(Theta))
        Y_err = (Y_est - Y)
        Y_err = Y_err * R

        grad_X = Y_err.dot(Theta)
        grad_Theta = np.dot(np.transpose(Y_err), X)

        # regularization term
        grad_X += lambd * X
        grad_Theta += lambd * Theta

        return flatten_params(grad_X, grad_Theta)

    df = pd.DataFrame(list(Myrating.objects.all().values()))

    number_of_users = df.user_id.unique().shape[0]
    number_of_movies = df.movie_id.unique().shape[0]
    number_of_features = 10

    Y_cur = np.zeros((number_of_movies, number_of_users))
    for row in df.itertuples():
        #movie = Movie.objects.get(id=row[2])
        #m_id = movie.movie_id
        Y_cur[row[2] - 1, row[4] - 1] = row[3]

    R_cur = np.zeros((number_of_movies, number_of_users))
    for i in range(Y_cur.shape[0]):
        for j in range(Y_cur.shape[1]):
            if Y_cur[i][j] != 0:
                R_cur[i][j] = 1

    Ynorm, Ymean = normalize_ratings(Y_cur, R_cur)


    # Give small random initial values to X and Theta
    X_cur = np.random.rand(number_of_movies, number_of_features)
    Theta_cur = np.random.rand(number_of_users, number_of_features)

    # get params for cost function J(X(1), X(2), ... , X(number_of_movies), Theta(1), Theta(2), ..., Theta(number_of_users))
    params = flatten_params(X_cur, Theta_cur)

    # set lambda
    lambd = 0.0000000000001
    result = scipy.optimize.fmin_cg(cofi_cost_func, x0=params, fprime=cofi_grad,
                                    args=(Y_cur, R_cur, number_of_users, number_of_movies,
                                    number_of_features, lambd),maxiter=None, disp=True, full_output=True)


    predicted_X, predicted_Theta = reshape_params(result[0], number_of_movies, number_of_users, number_of_features)

    prediction_matrix = predicted_X.dot(predicted_Theta.T)

    return prediction_matrix, Ymean, predicted_X
