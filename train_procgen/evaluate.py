import tensorflow as tf
from baselines.ppo2 import ppo2
from baselines.common.models import build_impala_cnn
from baselines.common.mpi_util import setup_mpi_gpus
from procgen import ProcgenEnv
from baselines.common.vec_env import (
    VecExtractDictObs,
    VecMonitor,
    VecFrameStack,
    VecNormalize
)
from baselines import logger
from mpi4py import MPI
import argparse
from .alternate_ppo2 import alt_ppo2
import os

def eval_fn(load_path, env_name='fruitbot', distribution_mode='easy', num_levels=500, start_level=500, log_dir='./tmp/procgen', comm=None):
    learning_rate = 5e-4
    ent_coef = .01
    gamma = .999
    lam = .95
    nsteps = 256
    nminibatches = 8
    ppo_epochs = 3
    clip_range = .2
    use_vf_clipping = True
    
    mpi_rank_weight = 1
    
    log_comm = comm.Split(1 if is_test_worker else 0, 0)
    format_strs = ['csv', 'stdout'] if log_comm.Get_rank() == 0 else []
    logger.configure(comm=log_comm, dir=log_dir, format_strs=format_strs)

    logger.info("creating environment")
    venv = ProcgenEnv(num_envs=num_envs, env_name=env_name, num_levels=num_levels, start_level=start_level, distribution_mode=distribution_mode)
    venv = VecExtractDictObs(venv, "rgb")

    venv = VecMonitor(
        venv=venv, filename=None, keep_buf=100,
    )

    venv = VecNormalize(venv=venv, ob=False)
    
    logger.info("creating tf session")
    setup_mpi_gpus()
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True #pylint: disable=E1101
    sess = tf.Session(config=config)
    sess.__enter__()
    
    conv_fn = lambda x: build_impala_cnn(x, depths=[16,32,32], emb_size=256)
    ###
    runner = Runner(env = env, model = model, nsteps = nsteps, gamma = gamma, lam = lam)
    epinfobuf = deque(maxlen=100)
    eval_obs, eval_returns, eval_masks, eval_actions, eval_values, eval_neglogpacs, eval_states, eval_epinfos = eval_runner.run() #pylint: disable=E0632
    eval_epinfobuf.extend(eval_epinfos)
    logger.logkv('eval_eprewmean', safemean([epinfo['r'] for epinfo in eval_epinfobuf]) )
    logger.logkv('eval_eplenmean', safemean([epinfo['l'] for epinfo in eval_epinfobuf]) )
#(env_name, num_envs, distribution_mode, num_levels, start_level, timesteps_per_proc, is_test_worker=False, log_dir='./tmp/procgen', comm=None, alternate_ppo=False):
# load model
# run on val dataset
# >> print & log to csv?
# choose best model based on val results
# run best model on test
# >> print & log(?) result

# if model_fn is None:
#         from baselines.ppo2.model import Model
#         model_fn = Model

#     model = model_fn(policy=policy, ob_space=ob_space, ac_space=ac_space, nbatch_act=nenvs, nbatch_train=nbatch_train,
#                     nsteps=nsteps, ent_coef=ent_coef, vf_coef=vf_coef,
#                     max_grad_norm=max_grad_norm, comm=comm, mpi_rank_weight=mpi_rank_weight)

#     if load_path is not None:
#         model.load(load_path)
#     # Instantiate the runner object
#     runner = Runner(env=env, model=model, nsteps=nsteps, gamma=gamma, lam=lam)
#     if eval_env is not None:
#         eval_runner = Runner(env = eval_env, model = model, nsteps = nsteps, gamma = gamma, lam= lam)

    conv_fn = lambda x: build_impala_cnn(x, depths=[16,32,32], emb_size=256)

    logger.info("training")
    if alternate_ppo:
        alt_ppo2.learn(
            env=venv,
            network=conv_fn,
            total_timesteps=timesteps_per_proc,
            load_path=load_path,
            save_interval=1,
            nsteps=nsteps,
            nminibatches=nminibatches,
            lam=lam,
            gamma=gamma,
            noptepochs=ppo_epochs,
            log_interval=1,
            ent_coef=ent_coef,
            mpi_rank_weight=mpi_rank_weight,
            clip_vf=use_vf_clipping,
            comm=comm,
            lr=learning_rate,
            cliprange=clip_range,
            update_fn=None,
            init_fn=None,
            vf_coef=0.5,
            max_grad_norm=0.5,
        )
    else:
        ppo2.learn(
            env=venv,
            network=conv_fn,
            total_timesteps=timesteps_per_proc,
            load_path=load_path,
            save_interval=1,
            nsteps=nsteps,
            nminibatches=nminibatches,
            lam=lam,
            gamma=gamma,
            noptepochs=ppo_epochs,
            log_interval=1,
            ent_coef=ent_coef,
            mpi_rank_weight=mpi_rank_weight,
            clip_vf=use_vf_clipping,
            comm=comm,
            lr=learning_rate,
            cliprange=clip_range,
            update_fn=None,
            init_fn=None,
            vf_coef=0.5,
            max_grad_norm=0.5,
        )
    #   for chkpts in train_# path given in load_model args:
    #       calculate loss and average rewards in ppo_metrics
    #       find optimal model based on min loss
    #   return optimal model

def model_avg_loss(env, model):
    
    
def optimal_chkpt(path, model, env):
    best_loss = float("inf")
    best_chkpt = None
    for chkpt in os.listdir(path):
        model.load(path + chkpt)
        curr_loss = model_avg_loss(env, model)
        if curr_loss < best_loss:
            best_loss = curr_loss
            best_chkpt = path + chkpt
    return best_chkpt

def main():
    parser = argparse.ArgumentParser(description='Process procgen evaluation arguments.')
    parser.add_argument('--load_model', type=str, required=True)
    parser.add_argument('--log_dir', type=str, default='./logs/eval')
    parser.add_argument('--env_name', type=str, default='fruitbot')
    parser.add_argument('--distribution_mode', type=str, default='easy', choices=["easy", "hard", "exploration", "memory", "extreme"])
    parser.add_argument('--num_levels', type=int, default=500)
    parser.add_argument('--start_level', type=int, default=500)

    args = parser.parse_args()

    comm = MPI.COMM_WORLD 

    eval_fn(args.load_path,
            log_dir=args.log_dir,
            env_name=args.env_name,
            distribution_mode=args.distribution_mode,
            num_levels=args.num_levels,
            start_level=args.start_level,
            comm=comm,
           )
    args.env_name,
        args.num_envs,
        args.distribution_mode,
        args.num_levels,
        args.start_level,
        args.timesteps_per_proc,
        is_test_worker=is_test_worker,
        log_dir=args.log_dir,
        comm=comm,
        alternate_ppo=args.alternate_ppo,
        )


if __name__ == '__main__':
    main()
